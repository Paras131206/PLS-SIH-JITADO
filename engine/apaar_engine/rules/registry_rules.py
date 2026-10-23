"""engine/apaar_engine/rules/registry_rules.py

APAAR registry verification rules:
- V003: apaar_id not found in the (mock) APAAR registry
- V004: APAAR registry name/DOB does not match uploaded name/DOB (fuzzy)

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

import pandas as pd
from rapidfuzz import fuzz

from apaar_engine.models import Issue, Severity, mask_apaar
from apaar_engine.rules.registry import register_rule

HONORIFICS = re.compile(r"^(shri|smt|kumari|dr|mr|mrs|ms)\b\.?\s*", re.IGNORECASE)


def normalize_person_name(name: str) -> str:
    """Normalize Indian person name for fuzzy comparison."""
    if not name:
        return ""
    # Strip honorifics
    clean = HONORIFICS.sub("", name.strip())
    # Remove punctuation, lower, collapse spaces
    clean = re.sub(r"[^\w\s]", " ", clean).lower()
    return " ".join(clean.split())


@register_rule("V003")
def validate_v003_registry_lookup(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    registry: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V003: apaar_id not found in the (mock) APAAR registry."""
    issues: List[Issue] = []
    if registry is None or "apaar_id" not in df.columns or df.empty:
        return issues

    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))
    apaar_series = df["apaar_id"].fillna("").astype(str).str.strip()

    for r_num, apaar in zip(row_nums, apaar_series):
        if len(apaar) == 12 and apaar.isdigit():
            rec = registry.lookup(apaar)
            if rec is None:
                issues.append(
                    Issue(
                        row=int(r_num),
                        field="apaar_id",
                        rule_id="V003",
                        severity=Severity.ERROR,
                        message=f"apaar_id '{mask_apaar(apaar)}' not found in APAAR registry",
                        value_masked=mask_apaar(apaar),
                    )
                )
    return issues


@register_rule("V004")
def validate_v004_registry_fuzzy_match(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    registry: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V004: APAAR registry name/DOB does not match uploaded name/DOB (fuzzy)."""
    issues: List[Issue] = []
    if registry is None or df.empty:
        return issues

    required_cols = ["apaar_id", "full_name", "dob"]
    if not all(c in df.columns for c in required_cols):
        return issues

    threshold = rule_meta.get("params", {}).get("name_similarity_threshold", 0.85)
    row_nums = df["_row_num"] if "_row_num" in df.columns else pd.Series(range(2, len(df) + 2))

    for r_num, apaar, up_name, up_dob in zip(
        row_nums,
        df["apaar_id"].fillna("").astype(str).str.strip(),
        df["full_name"].fillna("").astype(str).str.strip(),
        df["dob"].fillna("").astype(str).str.strip(),
    ):
        if len(apaar) == 12 and apaar.isdigit():
            rec = registry.lookup(apaar)
            if rec is not None:
                reg_name = str(rec.get("name") or rec.get("full_name") or "").strip()
                reg_dob = str(rec.get("dob") or "").strip()

                # 1. Exact DOB check (only for valid parseable dates)
                up_dt = pd.to_datetime(up_dob, format="%Y-%m-%d", errors="coerce")
                reg_dt = pd.to_datetime(reg_dob, format="%Y-%m-%d", errors="coerce")
                if not pd.isna(up_dt) and not pd.isna(reg_dt) and up_dt != reg_dt:
                    issues.append(
                        Issue(
                            row=int(r_num),
                            field="dob",
                            rule_id="V004",
                            severity=Severity.WARN,
                            message=(
                                f"APAAR registry DOB '{reg_dob}' does not match "
                                f"uploaded DOB '{up_dob}'"
                            ),
                        )
                    )

                # 2. Fuzzy Name check using rapidfuzz token_set_ratio
                if up_name and reg_name:
                    norm_up = normalize_person_name(up_name)
                    norm_reg = normalize_person_name(reg_name)
                    score = fuzz.token_set_ratio(norm_up, norm_reg) / 100.0
                    if score < threshold:
                        issues.append(
                            Issue(
                                row=int(r_num),
                                field="full_name",
                                rule_id="V004",
                                severity=Severity.WARN,
                                message=(
                                    f"APAAR registry name '{reg_name}' does not match "
                                    f"uploaded name '{up_name}' "
                                    f"(fuzzy similarity {score:.2f} < {threshold})"
                                ),
                            )
                        )
    return issues
