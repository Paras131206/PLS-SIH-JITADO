"""engine/apaar_engine/rules/schema_rules.py

Vectorized implementations of Phase 1 validation rules:
- V001: Required column missing from file header
- V002: apaar_id missing or not 12 digits
- V005: Required field null or empty
- V006: Invalid format (date, enum, email, mobile, ISO country)
- V007: Duplicate apaar_id within the batch
- V008: Duplicate institution_student_id within institution and year

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

import pandas as pd

from apaar_engine.models import Issue, Severity, mask_apaar
from apaar_engine.rules.registry import register_rule

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MOBILE_REGEX = re.compile(r"^[6-9][0-9]{9}$")
ISO2_REGEX = re.compile(r"^[A-Z]{2}$")

VALID_ENUMS: Dict[str, set[str]] = {
    "gender": {"M", "F", "T"},
    "category": {"GEN", "EWS", "OBC-NCL", "SC", "ST"},
    "course_level": {"DIPLOMA", "UG", "PG", "PGDM", "PHD"},
    "admission_type": {"REGULAR", "LATERAL", "TRANSFER"},
    "seat_type": {"REGULAR", "SUPERNUMERARY"},
    "supernumerary_scheme": {"TFW", "PMSSS", "JK", "NE", "FN_OCI_NRI", "OTHER", ""},
    "quota": {"NONE", "NRI", "OCI", "FN", "PIO", "CIWG"},
    "enrolment_status": {"ACTIVE", "WITHDRAWN", "DEFERRED", "COMPLETED"},
    "consent_status": {"GRANTED", "REFUSED", "WITHDRAWN"},
}

CANONICAL_REQUIRED_COLUMNS = [
    "apaar_id",
    "institution_aicte_id",
    "institution_student_id",
    "full_name",
    "dob",
    "gender",
    "category",
    "program_code",
    "course_level",
    "academic_year",
    "admission_date",
    "admission_type",
    "seat_type",
    "quota",
    "nationality",
    "nri_status",
    "oci_status",
    "fn_status",
    "enrolment_status",
    "consent_status",
]


@register_rule("V001")
def validate_v001_header(df: pd.DataFrame, rule_meta: Dict[str, Any], **kwargs: Any) -> List[Issue]:
    """V001: Required column missing from file header."""
    issues: List[Issue] = []
    required_cols = (
        rule_meta.get("params", {}).get("required_columns") or CANONICAL_REQUIRED_COLUMNS
    )

    present_cols = set(df.columns)
    for col in required_cols:
        if col not in present_cols:
            issues.append(
                Issue(
                    row=1,
                    field=col,
                    rule_id="V001",
                    severity=Severity.ERROR,
                    message=f"Required column '{col}' missing from file header",
                )
            )
    return issues


@register_rule("V002")
def validate_v002_apaar(df: pd.DataFrame, rule_meta: Dict[str, Any], **kwargs: Any) -> List[Issue]:
    """V002: apaar_id missing or not 12 digits."""
    issues: List[Issue] = []
    if "apaar_id" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    raw_col = df["apaar_id"].fillna("").astype(str).str.strip()

    # Invalid if not exactly 12 digits or contains non-digits
    invalid_mask = (raw_col.str.len() != 12) | (~raw_col.str.isdigit())

    if invalid_mask.any():
        for r_num, raw_val in zip(row_nums[invalid_mask], raw_col[invalid_mask]):
            masked = mask_apaar(raw_val) if raw_val else None
            issues.append(
                Issue(
                    row=int(r_num),
                    field="apaar_id",
                    rule_id="V002",
                    severity=Severity.ERROR,
                    message="apaar_id missing or not 12 digits",
                    value_masked=masked,
                )
            )
    return issues


@register_rule("V005")
def validate_v005_required_fields(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V005: Required field null or empty."""
    issues: List[Issue] = []
    if df.empty:
        return issues

    # Columns that cannot be empty (exclude apaar_id if already handled or include it)
    required_fields = rule_meta.get("fields") or CANONICAL_REQUIRED_COLUMNS
    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))

    for col in required_fields:
        if col not in df.columns:
            continue
        raw_series = df[col].fillna("").astype(str).str.strip()
        if col == "quota":
            empty_mask = df[col].isna() | (raw_series == "")
        else:
            empty_mask = (
                df[col].isna()
                | (raw_series == "")
                | (raw_series.str.lower().isin(["nan", "null", "none"]))
            )

        if empty_mask.any():
            for r_num in row_nums[empty_mask]:
                issues.append(
                    Issue(
                        row=int(r_num),
                        field=col,
                        rule_id="V005",
                        severity=Severity.ERROR,
                        message=f"Required field '{col}' is null or empty",
                    )
                )
    return issues


@register_rule("V006")
def validate_v006_format(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V006: Invalid format (date, enum, email, mobile, ISO country)."""
    issues: List[Issue] = []
    if df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))

    # 1. Date format validation (YYYY-MM-DD)
    date_cols = ["dob", "admission_date", "consent_date"]
    for d_col in date_cols:
        if d_col not in df.columns:
            continue
        raw_dates = df[d_col].fillna("").astype(str).str.strip()
        non_empty_mask = (raw_dates != "") & (~raw_dates.str.lower().isin(["nan", "none", "null"]))

        if non_empty_mask.any():
            parsed_dates = pd.to_datetime(
                raw_dates[non_empty_mask], format="%Y-%m-%d", errors="coerce"
            )
            invalid_date_mask = parsed_dates.isna()
            if invalid_date_mask.any():
                invalid_indices = raw_dates[non_empty_mask][invalid_date_mask].index
                for idx in invalid_indices:
                    issues.append(
                        Issue(
                            row=int(row_nums.loc[idx]),
                            field=d_col,
                            rule_id="V006",
                            severity=Severity.ERROR,
                            message=(
                                f"Invalid date format for '{d_col}': '{raw_dates.loc[idx]}' "
                                f"(expected YYYY-MM-DD)"
                            ),
                        )
                    )

    # 2. Enum validations
    for enum_col, allowed_vals in VALID_ENUMS.items():
        if enum_col not in df.columns:
            continue
        raw_vals = df[enum_col].fillna("").astype(str).str.strip()
        # For supernumerary_scheme, empty is allowed
        if enum_col == "supernumerary_scheme":
            check_mask = (raw_vals != "") & (~raw_vals.str.lower().isin(["nan", "none", "null"]))
        else:
            check_mask = raw_vals != ""

        invalid_mask = check_mask & (~raw_vals.isin(allowed_vals))
        if invalid_mask.any():
            for r_num, bad_val in zip(row_nums[invalid_mask], raw_vals[invalid_mask]):
                issues.append(
                    Issue(
                        row=int(r_num),
                        field=enum_col,
                        rule_id="V006",
                        severity=Severity.ERROR,
                        message=f"Invalid enum value '{bad_val}' for '{enum_col}'",
                    )
                )

    # 3. ISO-3166-1 alpha-2 country validation
    if "nationality" in df.columns:
        nat_vals = df["nationality"].fillna("").astype(str).str.strip()
        non_empty = nat_vals != ""
        invalid_nat = non_empty & (~nat_vals.str.match(ISO2_REGEX))
        if invalid_nat.any():
            for r_num, bad_val in zip(row_nums[invalid_nat], nat_vals[invalid_nat]):
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="nationality",
                        rule_id="V006",
                        severity=Severity.ERROR,
                        message=(
                            f"Invalid nationality '{bad_val}' (must be 2-letter ISO country code)"
                        ),
                    )
                )

    # 4. Email format validation (optional field, but if present must be valid)
    if "email" in df.columns:
        emails = df["email"].fillna("").astype(str).str.strip()
        non_empty_email = (emails != "") & (~emails.str.lower().isin(["nan", "none", "null"]))
        invalid_email = non_empty_email & (~emails.str.match(EMAIL_REGEX))
        if invalid_email.any():
            for r_num, bad_val in zip(row_nums[invalid_email], emails[invalid_email]):
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="email",
                        rule_id="V006",
                        severity=Severity.ERROR,
                        message=f"Invalid email format: '{bad_val}'",
                    )
                )

    # 5. Mobile format validation (optional field; if present must be 10 digits starting 6-9)
    if "mobile" in df.columns:
        mobiles = df["mobile"].fillna("").astype(str).str.strip()
        non_empty_mobile = (mobiles != "") & (~mobiles.str.lower().isin(["nan", "none", "null"]))
        invalid_mobile = non_empty_mobile & (~mobiles.str.match(MOBILE_REGEX))
        if invalid_mobile.any():
            for r_num, bad_val in zip(row_nums[invalid_mobile], mobiles[invalid_mobile]):
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="mobile",
                        rule_id="V006",
                        severity=Severity.ERROR,
                        message=(
                            f"Invalid mobile format: '{bad_val}' "
                            f"(must be 10 digits starting with 6-9)"
                        ),
                    )
                )

    return issues


@register_rule("V007")
def validate_v007_duplicate_apaar(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V007: Duplicate apaar_id within the batch."""
    issues: List[Issue] = []
    if "apaar_id" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    raw_col = df["apaar_id"].fillna("").astype(str).str.strip()
    valid_apaars = (raw_col != "") & (~raw_col.str.lower().isin(["nan", "none", "null"]))

    # Find duplicates among non-empty values
    dup_mask = valid_apaars & raw_col.duplicated(keep=False)
    if dup_mask.any():
        for r_num, val in zip(row_nums[dup_mask], raw_col[dup_mask]):
            issues.append(
                Issue(
                    row=int(r_num),
                    field="apaar_id",
                    rule_id="V007",
                    severity=Severity.ERROR,
                    message=f"Duplicate apaar_id '{mask_apaar(val)}' within batch",
                    value_masked=mask_apaar(val),
                )
            )
    return issues


@register_rule("V008")
def validate_v008_duplicate_student_id(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V008: Duplicate institution_student_id within institution and year."""
    issues: List[Issue] = []
    req_cols = ["institution_aicte_id", "academic_year", "institution_student_id"]
    if not all(c in df.columns for c in req_cols) or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    std_id_col = df["institution_student_id"].fillna("").astype(str).str.strip()
    non_empty = (std_id_col != "") & (~std_id_col.str.lower().isin(["nan", "none", "null"]))

    dup_mask = non_empty & df.duplicated(subset=req_cols, keep=False)
    if dup_mask.any():
        for r_num, sid, inst, year in zip(
            row_nums[dup_mask],
            std_id_col[dup_mask],
            df.loc[dup_mask, "institution_aicte_id"],
            df.loc[dup_mask, "academic_year"],
        ):
            issues.append(
                Issue(
                    row=int(r_num),
                    field="institution_student_id",
                    rule_id="V008",
                    severity=Severity.ERROR,
                    message=(
                        f"Duplicate student ID '{sid}' within institution '{inst}' "
                        f"and academic year '{year}'"
                    ),
                )
            )
    return issues
