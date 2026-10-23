"""engine/apaar_engine/validate.py

Main batch validation pipeline for APAAR-SDMS.
Pure, in-memory validation: validate_batch(file_or_df, intake_df, registry, history) -> BatchReport.

Quality score calculation:
- completeness: 0.25
- validity: 0.35
- uniqueness: 0.20
- consistency: 0.20

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import pandas as pd

from apaar_engine.models import (
    Anomaly,
    BatchReport,
    DuplicateCluster,
    IntakeSummary,
    Issue,
    Severity,
)
from apaar_engine.parser import parse_file
from apaar_engine.rules.registry import load_rule_catalog, run_rule
from apaar_engine.rules.schema_rules import CANONICAL_REQUIRED_COLUMNS

# ---------------------------------------------------------------------------
# Quality Score Weight Configuration (Deequ-style 4-dimension metric)
# Documented per agents.md §10 / Phase 2 specifications.
# ---------------------------------------------------------------------------
QUALITY_WEIGHTS = {
    "completeness": 0.25,  # Non-null values across required canonical fields
    "validity": 0.35,  # Rows with valid format, headers, schema (V001, V002, V005, V006)
    "uniqueness": 0.20,  # Unique records without batch duplicate collisions (V007, V008)
    "consistency": 0.20,  # Records conforming to intake limits, policy, consent (V012-V019)
}


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
            non_empty = series[(series != "") & (~series.str.lower().isin(["nan", "null"]))]
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


def calculate_quality_score(
    df: pd.DataFrame,
    issues: List[Issue],
    metrics: Dict[str, Dict[str, float]],
) -> float:
    """Calculate weighted batch quality score (0.0 to 100.0).

    Dimensions:
    - completeness (weight 0.25): across canonical required fields
    - validity (weight 0.35): V001, V002, V005, V006
    - uniqueness (weight 0.20): V007, V008
    - consistency (weight 0.20): V012, V013, V014, V015, V016, V017, V018, V019
    """
    total_rows = len(df)
    if total_rows == 0:
        return 0.0

    # 1. Completeness score across required columns
    comp_dict = metrics.get("completeness", {})
    req_comp = [v for k, v in comp_dict.items() if k in CANONICAL_REQUIRED_COLUMNS]
    if req_comp:
        completeness_score = sum(req_comp) / len(req_comp)
    elif comp_dict:
        completeness_score = sum(comp_dict.values()) / len(comp_dict)
    else:
        completeness_score = 1.0

    # 2. Categorize issues by row
    validity_error_rows: set[int] = set()
    uniqueness_error_rows: set[int] = set()
    consistency_error_rows: set[int] = set()

    for iss in issues:
        if iss.severity != Severity.ERROR or iss.row is None or iss.row < 2:
            continue
        rid = iss.rule_id
        if rid in ("V001", "V002", "V005", "V006"):
            validity_error_rows.add(iss.row)
        elif rid in ("V007", "V008"):
            uniqueness_error_rows.add(iss.row)
        elif rid in ("V012", "V013", "V014", "V015", "V017", "V018", "V019"):
            consistency_error_rows.add(iss.row)

    validity_score = max(0.0, 1.0 - (len(validity_error_rows) / total_rows))
    uniqueness_score = max(0.0, 1.0 - (len(uniqueness_error_rows) / total_rows))
    consistency_score = max(0.0, 1.0 - (len(consistency_error_rows) / total_rows))

    weighted = (
        QUALITY_WEIGHTS["completeness"] * completeness_score
        + QUALITY_WEIGHTS["validity"] * validity_score
        + QUALITY_WEIGHTS["uniqueness"] * uniqueness_score
        + QUALITY_WEIGHTS["consistency"] * consistency_score
    )
    return round(weighted * 100.0, 2)


def generate_intake_summaries(
    df: pd.DataFrame,
    intake_df: Optional[pd.DataFrame],
    inst_id: Optional[str] = None,
) -> List[IntakeSummary]:
    """Generate per-program intake summary:
    approved, enrolled_regular, supernumerary by scheme, excess.
    """
    summaries: List[IntakeSummary] = []
    if intake_df is None or df.empty or "program_code" not in df.columns:
        return summaries

    has_inst = "institution_aicte_id" in df.columns and "institution_aicte_id" in intake_df.columns
    filter_inst = (
        inst_id
        if (
            has_inst
            and inst_id
            and inst_id != "UNKNOWN"
            and inst_id in intake_df["institution_aicte_id"].values
        )
        else None
    )

    if filter_inst:
        sub_intake = intake_df[intake_df["institution_aicte_id"] == filter_inst]
        sub_df = df[df["institution_aicte_id"] == filter_inst]
    else:
        sub_intake = intake_df
        sub_df = df

    intake_programs = sub_intake["program_code"].dropna().unique()
    batch_programs = sub_df["program_code"].dropna().unique()
    all_programs = sorted(set(intake_programs) | set(batch_programs))

    seat_types = (
        sub_df["seat_type"].fillna("REGULAR").astype(str).str.strip().str.upper()
        if "seat_type" in sub_df.columns
        else pd.Series(["REGULAR"] * len(sub_df), index=sub_df.index)
    )
    schemes = (
        sub_df["supernumerary_scheme"].fillna("").astype(str).str.strip().str.upper()
        if "supernumerary_scheme" in sub_df.columns
        else pd.Series([""] * len(sub_df), index=sub_df.index)
    )

    for prog in all_programs:
        prog_str = str(prog).strip()
        matched_intake = sub_intake[sub_intake["program_code"] == prog_str]
        approved = int(matched_intake["approved_intake"].sum()) if not matched_intake.empty else 0

        prog_mask = sub_df["program_code"] == prog_str
        total_enrolled = int(prog_mask.sum())

        supernumerary_mask = prog_mask & (seat_types == "SUPERNUMERARY")
        supernumerary_count = int(supernumerary_mask.sum())
        regular_count = total_enrolled - supernumerary_count

        # Scheme breakdown
        supernumerary_by_scheme: Dict[str, int] = {}
        if supernumerary_count > 0:
            prog_schemes = schemes[supernumerary_mask]
            for sch in prog_schemes.unique():
                if sch and sch not in ("NONE", "NULL", "NAN"):
                    supernumerary_by_scheme[sch] = int((prog_schemes == sch).sum())

        excess = max(0, regular_count - approved)

        summaries.append(
            IntakeSummary(
                program_code=prog_str,
                approved=approved,
                enrolled=total_enrolled,
                supernumerary=supernumerary_count,
                excess=excess,
                enrolled_regular=regular_count,
                supernumerary_by_scheme=supernumerary_by_scheme,
            )
        )

    return summaries


def validate_batch(
    file_or_df: Union[str, Path, bytes, BinaryIO, io.TextIOBase, pd.DataFrame],
    intake_df: Optional[pd.DataFrame] = None,
    registry: Optional[Any] = None,
    history: Optional[Any] = None,
    central_df: Optional[pd.DataFrame] = None,
    peer_history: Optional[Any] = None,
    batch_id: Optional[str] = None,
    institution_aicte_id: Optional[str] = None,
) -> BatchReport:
    """Validate an uploaded batch against canonical schema and rule catalog V001–V020.

    - Stays pure (no direct DB/HTTP dependencies).
    - Rules requiring registry/history/central_df are skipped when those are None.
    """
    if batch_id is None:
        batch_id = str(uuid.uuid4())

    all_issues: List[Issue] = []
    duplicate_clusters: List[DuplicateCluster] = []
    anomalies: List[Anomaly] = []

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

    # 4. Run Rules
    # Schema & header rules
    all_issues.extend(run_rule("V001", df, catalog=catalog))
    all_issues.extend(run_rule("V002", df, catalog=catalog))
    all_issues.extend(run_rule("V005", df, catalog=catalog))
    all_issues.extend(run_rule("V006", df, catalog=catalog))
    all_issues.extend(run_rule("V007", df, catalog=catalog))
    all_issues.extend(run_rule("V008", df, catalog=catalog))

    # Consistency rules
    all_issues.extend(run_rule("V014", df, catalog=catalog))
    all_issues.extend(run_rule("V015", df, catalog=catalog))
    all_issues.extend(run_rule("V016", df, catalog=catalog))
    all_issues.extend(run_rule("V017", df, catalog=catalog))
    all_issues.extend(run_rule("V018", df, catalog=catalog))

    # Intake rules (require intake_df)
    if intake_df is not None:
        all_issues.extend(run_rule("V019", df, catalog=catalog, intake_df=intake_df))
        all_issues.extend(run_rule("V012", df, catalog=catalog, intake_df=intake_df))
        all_issues.extend(run_rule("V013", df, catalog=catalog, intake_df=intake_df))

    # Registry rules (require registry)
    if registry is not None:
        all_issues.extend(run_rule("V003", df, catalog=catalog, registry=registry))
        all_issues.extend(run_rule("V004", df, catalog=catalog, registry=registry))

    # Intra-batch dedup rule (V009)
    all_issues.extend(run_rule("V009", df, catalog=catalog, cluster_collector=duplicate_clusters))

    # Cross-institution dedup rules (V010, V011)
    if central_df is not None:
        all_issues.extend(
            run_rule(
                "V010",
                df,
                catalog=catalog,
                central_df=central_df,
                cluster_collector=duplicate_clusters,
            )
        )
        all_issues.extend(
            run_rule(
                "V011",
                df,
                catalog=catalog,
                central_df=central_df,
                cluster_collector=duplicate_clusters,
            )
        )

    # Metric history anomaly rules (V020)
    if history is not None or peer_history is not None:
        all_issues.extend(
            run_rule(
                "V020",
                df,
                catalog=catalog,
                history=history,
                peer_history=peer_history,
                intake_df=intake_df,
                anomaly_collector=anomalies,
            )
        )

    # 5. Row-level classification
    rows_total = len(df)
    error_rows: set[int] = set()
    warn_rows: set[int] = set()

    for issue in all_issues:
        if issue.row is not None and issue.row >= 2:
            if issue.severity == Severity.ERROR:
                error_rows.add(issue.row)
            elif issue.severity == Severity.WARN:
                warn_rows.add(issue.row)

    pure_warn_rows = warn_rows - error_rows
    rows_error = len(error_rows)
    rows_warning = len(pure_warn_rows)
    rows_valid = max(0, rows_total - rows_error)

    # 6. Column metrics & weighted quality score
    metrics = compute_batch_metrics(df)
    quality_score = calculate_quality_score(df, all_issues, metrics)

    # 7. Intake summary per program
    intake_summary = generate_intake_summaries(df, intake_df, inst_id=inst_id)

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
        duplicate_clusters=duplicate_clusters,
        anomalies=anomalies,
    )
