"""engine/apaar_engine/rules/consistency_rules.py

Consistency and policy validation rules:
- V014: Quota/nationality inconsistent (OCI or FN with IN, NRI flag mismatch)
- V015: seat_type=SUPERNUMERARY with no scheme, or a scheme on a regular seat
- V016: Age implausible for course_level
- V017: admission_date outside the academic-year window
- V018: consent_status missing; or under 18 without guardian_consent

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

import pandas as pd

from apaar_engine.models import Issue, Severity
from apaar_engine.rules.registry import register_rule

COURSE_LEVEL_AGE_RANGES = {
    "DIPLOMA": {"min": 14, "max": 40},
    "UG": {"min": 16, "max": 35},
    "PG": {"min": 19, "max": 55},
    "PGDM": {"min": 19, "max": 55},
    "PHD": {"min": 21, "max": 65},
}


def parse_bool_series(series: pd.Series) -> pd.Series:
    """Normalize boolean series from strings/bools."""
    clean = series.fillna("").astype(str).str.strip().str.lower()
    return clean.isin(["true", "1", "yes", "t", "y"])


@register_rule("V014")
def validate_v014_quota_nationality(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V014: Quota/nationality inconsistent (OCI or FN with IN, NRI flag mismatch)."""
    issues: List[Issue] = []
    required_cols = ["quota", "nationality", "nri_status", "oci_status", "fn_status"]
    if not all(c in df.columns for c in required_cols) or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    quotas = df["quota"].fillna("").astype(str).str.strip().str.upper()
    nationalities = df["nationality"].fillna("").astype(str).str.strip().str.upper()
    nri_flags = parse_bool_series(df["nri_status"])
    oci_flags = parse_bool_series(df["oci_status"])
    fn_flags = parse_bool_series(df["fn_status"])

    for idx in df.index:
        r_num = int(row_nums.loc[idx])
        quota = quotas.loc[idx]
        nat = nationalities.loc[idx]
        is_nri = nri_flags.loc[idx]
        is_oci = oci_flags.loc[idx]
        is_fn = fn_flags.loc[idx]

        # 1. OCI status or OCI quota cannot have Indian nationality
        if (is_oci or quota == "OCI") and nat == "IN":
            issues.append(
                Issue(
                    row=r_num,
                    field="nationality",
                    rule_id="V014",
                    severity=Severity.ERROR,
                    message=(
                        "OCI status/quota requires non-Indian nationality "
                        "(nationality cannot be 'IN')"
                    ),
                )
            )

        # 2. FN status or FN quota cannot have Indian nationality
        if (is_fn or quota == "FN") and nat == "IN":
            issues.append(
                Issue(
                    row=r_num,
                    field="nationality",
                    rule_id="V014",
                    severity=Severity.ERROR,
                    message="Foreign National status/quota cannot have Indian nationality ('IN')",
                )
            )

        # 3. NRI quota requires nri_status=True
        if quota == "NRI" and not is_nri:
            issues.append(
                Issue(
                    row=r_num,
                    field="nri_status",
                    rule_id="V014",
                    severity=Severity.ERROR,
                    message="Quota is NRI but nri_status is False",
                )
            )

        # 4. nri_status=True requires quota to be NRI or CIWG
        if is_nri and quota not in ("NRI", "CIWG"):
            issues.append(
                Issue(
                    row=r_num,
                    field="quota",
                    rule_id="V014",
                    severity=Severity.ERROR,
                    message=f"nri_status is True but quota is '{quota}' (expected NRI or CIWG)",
                )
            )

    return issues


@register_rule("V015")
def validate_v015_seat_scheme(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V015: seat_type=SUPERNUMERARY with no scheme, or a scheme on a regular seat."""
    issues: List[Issue] = []
    required_cols = ["seat_type", "supernumerary_scheme"]
    if not all(c in df.columns for c in required_cols) or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    seat_types = df["seat_type"].fillna("").astype(str).str.strip().str.upper()
    schemes = df["supernumerary_scheme"].fillna("").astype(str).str.strip()

    # Mask for missing scheme
    empty_scheme = (schemes == "") | (schemes.str.lower().isin(["nan", "null", "none"]))

    # 1. SUPERNUMERARY with no scheme
    missing_scheme_mask = (seat_types == "SUPERNUMERARY") & empty_scheme
    if missing_scheme_mask.any():
        for r_num in row_nums[missing_scheme_mask]:
            issues.append(
                Issue(
                    row=int(r_num),
                    field="supernumerary_scheme",
                    rule_id="V015",
                    severity=Severity.ERROR,
                    message="seat_type is SUPERNUMERARY but supernumerary_scheme is missing",
                )
            )

    # 2. Scheme on REGULAR seat
    scheme_on_regular_mask = (seat_types == "REGULAR") & (~empty_scheme)
    if scheme_on_regular_mask.any():
        for r_num, sch in zip(row_nums[scheme_on_regular_mask], schemes[scheme_on_regular_mask]):
            issues.append(
                Issue(
                    row=int(r_num),
                    field="supernumerary_scheme",
                    rule_id="V015",
                    severity=Severity.ERROR,
                    message=f"Supernumerary scheme '{sch}' assigned to a REGULAR seat",
                )
            )

    return issues


@register_rule("V016")
def validate_v016_age_course_level(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V016: Age implausible for course_level."""
    issues: List[Issue] = []
    required_cols = ["dob", "course_level"]
    if not all(c in df.columns for c in required_cols) or df.empty:
        return issues

    age_ranges = rule_meta.get("params", {}).get("age_ranges") or COURSE_LEVEL_AGE_RANGES
    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))

    dob_series = pd.to_datetime(df["dob"], format="%Y-%m-%d", errors="coerce")
    ref_dates = (
        pd.to_datetime(df["admission_date"], format="%Y-%m-%d", errors="coerce")
        if "admission_date" in df.columns
        else pd.Series([pd.Timestamp(date.today())] * len(df))
    )

    for idx in df.index:
        d_val = dob_series.loc[idx]
        r_val = ref_dates.loc[idx]
        if pd.isna(d_val) or pd.isna(r_val):
            continue

        c_level = str(df.loc[idx, "course_level"]).strip().upper()
        if c_level not in age_ranges:
            continue

        age_years = (r_val - d_val).days // 365
        limit = age_ranges[c_level]
        min_age, max_age = limit["min"], limit["max"]

        if age_years < min_age or age_years > max_age:
            issues.append(
                Issue(
                    row=int(row_nums.loc[idx]),
                    field="dob",
                    rule_id="V016",
                    severity=Severity.WARN,
                    message=(
                        f"Student age {age_years} is implausible for course_level '{c_level}' "
                        f"(expected {min_age}–{max_age} years)"
                    ),
                )
            )

    return issues


@register_rule("V017")
def validate_v017_admission_window(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V017: admission_date outside the academic-year window."""
    issues: List[Issue] = []
    required_cols = ["admission_date", "academic_year"]
    if not all(c in df.columns for c in required_cols) or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    adm_dates = pd.to_datetime(df["admission_date"], format="%Y-%m-%d", errors="coerce")

    for idx in df.index:
        adm_val = adm_dates.loc[idx]
        if pd.isna(adm_val):
            continue

        acad_str = str(df.loc[idx, "academic_year"]).strip()
        # Parse start year e.g. "2026-27" -> 2026
        try:
            start_year = int(acad_str[:4])
        except (ValueError, TypeError):
            continue

        # Standard AICTE window: May 1 of start year to April 30 of next year
        window_start = pd.Timestamp(year=start_year, month=5, day=1)
        window_end = pd.Timestamp(year=start_year + 1, month=4, day=30)

        if adm_val < window_start or adm_val > window_end:
            issues.append(
                Issue(
                    row=int(row_nums.loc[idx]),
                    field="admission_date",
                    rule_id="V017",
                    severity=Severity.ERROR,
                    message=(
                        f"admission_date '{adm_val.strftime('%Y-%m-%d')}' is outside the "
                        f"academic-year window ({window_start.strftime('%Y-%m-%d')} to "
                        f"{window_end.strftime('%Y-%m-%d')}) for '{acad_str}'"
                    ),
                )
            )

    return issues


@register_rule("V018")
def validate_v018_consent(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V018: consent_status missing; or under 18 without guardian_consent."""
    issues: List[Issue] = []
    if "consent_status" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    consent_series = df["consent_status"].fillna("").astype(str).str.strip().str.upper()

    dob_series = (
        pd.to_datetime(df["dob"], format="%Y-%m-%d", errors="coerce")
        if "dob" in df.columns
        else pd.Series([pd.NaT] * len(df))
    )
    adm_dates = (
        pd.to_datetime(df["admission_date"], format="%Y-%m-%d", errors="coerce")
        if "admission_date" in df.columns
        else pd.Series([pd.Timestamp(date.today())] * len(df))
    )
    guardian_flags = (
        parse_bool_series(df["guardian_consent"])
        if "guardian_consent" in df.columns
        else pd.Series([False] * len(df))
    )

    for idx in df.index:
        r_num = int(row_nums.loc[idx])
        c_status = consent_series.loc[idx]

        # 1. consent_status must be GRANTED
        if not c_status or c_status != "GRANTED":
            issues.append(
                Issue(
                    row=r_num,
                    field="consent_status",
                    rule_id="V018",
                    severity=Severity.ERROR,
                    message=f"consent_status is '{c_status or 'MISSING'}' (must be GRANTED)",
                )
            )

        # 2. If under 18 at admission date, guardian_consent is required
        dob_val = dob_series.loc[idx]
        adm_val = adm_dates.loc[idx]
        if not pd.isna(dob_val) and not pd.isna(adm_val):
            age_years = (adm_val - dob_val).days // 365
            if age_years < 18 and not guardian_flags.loc[idx]:
                issues.append(
                    Issue(
                        row=r_num,
                        field="guardian_consent",
                        rule_id="V018",
                        severity=Severity.ERROR,
                        message=(
                            f"Student is minor (age {age_years} at admission) but "
                            f"guardian_consent is not granted"
                        ),
                    )
                )

    return issues
