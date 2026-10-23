"""engine/apaar_engine/rules/intake_rules.py

Intake and program validation rules:
- V012: Regular-seat enrolment > approved_intake for the program
- V013: Supernumerary count > allowed for that scheme
- V019: program_code not in approved programs

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from apaar_engine.models import Issue, Severity
from apaar_engine.rules.registry import register_rule


def parse_supernumerary_dict(val: Any) -> Dict[str, int]:
    """Parse supernumerary_allowed field from JSON string or dict."""
    if isinstance(val, dict):
        return {str(k): int(v) for k, v in val.items()}
    if isinstance(val, str):
        clean = val.strip()
        if not clean:
            return {}
        try:
            parsed = json.loads(clean)
            if isinstance(parsed, dict):
                return {str(k): int(v) for k, v in parsed.items()}
        except Exception:
            return {}
    return {}


@register_rule("V019")
def validate_v019_approved_program(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    intake_df: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V019: program_code not in approved programs."""
    issues: List[Issue] = []
    if intake_df is None or "program_code" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    has_inst_col = (
        "institution_aicte_id" in df.columns and "institution_aicte_id" in intake_df.columns
    )

    if has_inst_col:
        approved_pairs = set(
            zip(
                intake_df["institution_aicte_id"].astype(str).str.strip(),
                intake_df["program_code"].astype(str).str.strip(),
            )
        )
        for r_num, inst, prog in zip(
            row_nums,
            df["institution_aicte_id"].fillna("").astype(str).str.strip(),
            df["program_code"].fillna("").astype(str).str.strip(),
        ):
            if prog and (inst, prog) not in approved_pairs:
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="program_code",
                        rule_id="V019",
                        severity=Severity.ERROR,
                        message=f"program_code '{prog}' is not approved for institution '{inst}'",
                    )
                )
    else:
        approved_programs = set(intake_df["program_code"].dropna().unique())
        prog_series = df["program_code"].fillna("").astype(str).str.strip()
        unapproved_mask = (prog_series != "") & (~prog_series.isin(approved_programs))
        if unapproved_mask.any():
            for r_num, prog in zip(row_nums[unapproved_mask], prog_series[unapproved_mask]):
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="program_code",
                        rule_id="V019",
                        severity=Severity.ERROR,
                        message=f"program_code '{prog}' is not in approved programs",
                    )
                )

    return issues


@register_rule("V012")
def validate_v012_regular_intake(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    intake_df: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V012: Regular-seat enrolment > approved_intake for the program."""
    issues: List[Issue] = []
    if intake_df is None or "program_code" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    seat_types = (
        df["seat_type"].fillna("REGULAR").astype(str).str.strip().str.upper()
        if "seat_type" in df.columns
        else pd.Series(["REGULAR"] * len(df))
    )
    has_inst = "institution_aicte_id" in df.columns and "institution_aicte_id" in intake_df.columns

    for _, intake_row in intake_df.iterrows():
        inst = str(intake_row.get("institution_aicte_id", "")).strip()
        prog = str(intake_row.get("program_code", "")).strip()
        approved_intake = int(intake_row.get("approved_intake", 0))

        if has_inst and inst:
            prog_mask = (
                (df["institution_aicte_id"] == inst)
                & (df["program_code"] == prog)
                & (seat_types != "SUPERNUMERARY")
            )
        else:
            prog_mask = (df["program_code"] == prog) & (seat_types != "SUPERNUMERARY")

        regular_count = int(prog_mask.sum())

        if regular_count > approved_intake:
            excess = regular_count - approved_intake
            matched_indices = df[prog_mask].index
            excess_indices = matched_indices[approved_intake:]
            for idx in excess_indices:
                r_num = row_nums.loc[idx]
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="approved_intake",
                        rule_id="V012",
                        severity=Severity.ERROR,
                        message=(
                            f"Regular enrolment ({regular_count}) exceeds approved intake "
                            f"({approved_intake}) for program '{prog}' by {excess}"
                        ),
                    )
                )
    return issues


@register_rule("V013")
def validate_v013_supernumerary_limits(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    intake_df: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V013: Supernumerary count > allowed for that scheme."""
    issues: List[Issue] = []
    required_cols = ["program_code", "seat_type", "supernumerary_scheme"]
    if intake_df is None or not all(c in df.columns for c in required_cols) or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    seat_types = df["seat_type"].fillna("").astype(str).str.strip().str.upper()
    schemes = df["supernumerary_scheme"].fillna("").astype(str).str.strip().str.upper()
    has_inst = "institution_aicte_id" in df.columns and "institution_aicte_id" in intake_df.columns

    for _, intake_row in intake_df.iterrows():
        inst = str(intake_row.get("institution_aicte_id", "")).strip()
        prog = str(intake_row.get("program_code", "")).strip()
        allowed_config = parse_supernumerary_dict(intake_row.get("supernumerary_allowed"))

        if has_inst and inst:
            prog_super_mask = (
                (df["institution_aicte_id"] == inst)
                & (df["program_code"] == prog)
                & (seat_types == "SUPERNUMERARY")
            )
        else:
            prog_super_mask = (df["program_code"] == prog) & (seat_types == "SUPERNUMERARY")

        if not prog_super_mask.any():
            continue

        prog_schemes = schemes[prog_super_mask].unique()
        for scheme in prog_schemes:
            if not scheme or scheme in ("NONE", "NULL", "NAN"):
                continue
            scheme_mask = prog_super_mask & (schemes == scheme)
            count = int(scheme_mask.sum())
            max_allowed = allowed_config.get(scheme, 0)

            if count > max_allowed:
                excess_indices = df[scheme_mask].index[max_allowed:]
                for idx in excess_indices:
                    issues.append(
                        Issue(
                            row=int(row_nums.loc[idx]),
                            field="supernumerary_scheme",
                            rule_id="V013",
                            severity=Severity.ERROR,
                            message=(
                                f"Supernumerary count ({count}) exceeds allowed limit "
                                f"({max_allowed}) for scheme '{scheme}' in program '{prog}'"
                            ),
                        )
                    )
    return issues
