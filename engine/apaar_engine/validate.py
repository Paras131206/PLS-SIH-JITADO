"""engine/apaar_engine/validate.py

Main batch validation pipeline for APAAR-SDMS.
Pure, in-memory validation: validate_batch(file_or_df, intake_df, registry, history) -> BatchReport.

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import pandas as pd

from apaar_engine.models import (
    BatchReport,
    IntakeSummary,
    Issue,
    Severity,
)
from apaar_engine.parser import parse_file
from apaar_engine.rules.registry import load_rule_catalog, run_rule


def compute_batch_metrics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Compute Deequ-style completeness and uniqueness metrics across DataFrame columns."""
    if df.empty:
        return {"completeness": {}, "uniqueness": {}}

    total_rows = len(df)
    completeness: Dict[str, float] = {}
    uniqueness: Dict[str, float] = {}

    for col in df.columns:
        if col.startswith("_"):
            continue
        series = df[col].fillna("").astype(str).str.strip()
        if col == "quota":
            non_empty = series[(series != "") & (~df[col].isna())]
        else:
            non_empty = series[
                (series != "") & (~series.str.lower().isin(["nan", "null"]))
            ]
        comp = len(non_empty) / total_rows if total_rows > 0 else 0.0
        completeness[col] = round(comp, 4)

        if len(non_empty) > 0:
            uniq = non_empty.nunique() / len(non_empty)
            uniqueness[col] = round(uniq, 4)
        else:
            uniqueness[col] = 0.0

    return {
        "completeness": completeness,
        "uniqueness": uniqueness,
    }


def validate_batch(
    file_or_df: Union[str, Path, bytes, BinaryIO, io.TextIOBase, pd.DataFrame],
    intake_df: Optional[pd.DataFrame] = None,
    registry: Optional[Any] = None,
    history: Optional[Any] = None,
    batch_id: Optional[str] = None,
    institution_aicte_id: Optional[str] = None,
) -> BatchReport:
    """Validate an uploaded batch against canonical schema and rule catalog V001–V020.

    - Stays pure (no direct DB/HTTP dependencies).
    - Rules requiring registry/history are skipped when those are None.
    """
    if batch_id is None:
        batch_id = str(uuid.uuid4())

    all_issues: List[Issue] = []

    # 1. Parse file if needed
    if isinstance(file_or_df, pd.DataFrame):
        df = file_or_df.copy()
        if "_row_num" not in df.columns:
            df["_row_num"] = range(2, len(df) + 2)
    else:
        df, parse_issues = parse_file(file_or_df)
        all_issues.extend(parse_issues)

    # 2. Determine institution AICTE ID
    inst_id = institution_aicte_id
    if not inst_id:
        if not df.empty and "institution_aicte_id" in df.columns:
            inst_series = df["institution_aicte_id"].dropna().astype(str).str.strip()
            inst_series = inst_series[inst_series != ""]
            if not inst_series.empty:
                inst_id = str(inst_series.mode().iloc[0])
    if not inst_id:
        inst_id = "UNKNOWN"

    # 3. Load rule catalog
    catalog = load_rule_catalog()

    # 4. Run Phase 1 rules
    # V001 Header check
    all_issues.extend(run_rule("V001", df, catalog=catalog))

    # V002 APAAR format
    all_issues.extend(run_rule("V002", df, catalog=catalog))

    # V005 Required fields
    all_issues.extend(run_rule("V005", df, catalog=catalog))

    # V006 Format checks (dates, enums, email, mobile, country)
    all_issues.extend(run_rule("V006", df, catalog=catalog))

    # V007 Duplicate APAAR within batch
    all_issues.extend(run_rule("V007", df, catalog=catalog))

    # V008 Duplicate Student ID within institution & year
    all_issues.extend(run_rule("V008", df, catalog=catalog))

    # Rules needing registry / history are conditionally executed:
    if registry is not None:
        all_issues.extend(run_rule("V003", df, catalog=catalog, registry=registry))
        all_issues.extend(run_rule("V004", df, catalog=catalog, registry=registry))

    if history is not None:
        all_issues.extend(run_rule("V020", df, catalog=catalog, history=history))

    # 5. Row-level aggregation
    rows_total = len(df)
    error_rows: set[int] = set()
    warn_rows: set[int] = set()

    for issue in all_issues:
        if issue.row is not None and issue.row >= 2:
            if issue.severity == Severity.ERROR:
                error_rows.add(issue.row)
            elif issue.severity == Severity.WARN:
                warn_rows.add(issue.row)

    # Warnings on rows that don't already have an error
    pure_warn_rows = warn_rows - error_rows

    rows_error = len(error_rows)
    rows_warning = len(pure_warn_rows)
    rows_valid = max(0, rows_total - rows_error)

    # 6. Quality score (0.0 to 100.0)
    if rows_total > 0:
        quality_score = round((rows_valid / rows_total) * 100.0, 2)
    else:
        quality_score = 0.0

    # 7. Column metrics
    metrics = compute_batch_metrics(df)

    # 8. Intake summary (skeleton for Phase 2)
    intake_summary: List[IntakeSummary] = []
    if intake_df is not None and not df.empty and "program_code" in df.columns:
        # Group by program_code
        programs = df["program_code"].dropna().unique()
        for prog in programs:
            enrolled = int((df["program_code"] == prog).sum())
            supernumerary = 0
            if "seat_type" in df.columns:
                supernumerary = int(
                    ((df["program_code"] == prog) & (df["seat_type"] == "SUPERNUMERARY")).sum()
                )
            regular = enrolled - supernumerary
            approved = 0
            if "approved_intake" in intake_df.columns:
                matched = intake_df[intake_df["program_code"] == prog]
                if not matched.empty:
                    approved = int(matched["approved_intake"].iloc[0])
            excess = max(0, regular - approved)
            intake_summary.append(
                IntakeSummary(
                    program_code=str(prog),
                    approved=approved,
                    enrolled=enrolled,
                    supernumerary=supernumerary,
                    excess=excess,
                )
            )

    return BatchReport(
        batch_id=batch_id,
        institution_aicte_id=inst_id,
        rows_total=rows_total,
        rows_valid=rows_valid,
        rows_warning=rows_warning,
        rows_error=rows_error,
        quality_score=quality_score,
        metrics=metrics,
        issues=all_issues,
        intake_summary=intake_summary,
        duplicate_clusters=[],
        anomalies=[],
    )
