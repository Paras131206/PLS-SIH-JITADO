"""engine/apaar_engine/anomaly/metrics.py

Deequ-style per-batch metric state:
- null rate per column
- duplicate rate
- nri/oci/fn share
- supernumerary share
- intake fill ratio
- total rows
- mergeable JSON state representation for streaming / multi-batch rollups

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class BatchMetricState(BaseModel):
    """Deequ-style per-batch metric state with merge semantics."""

    model_config = ConfigDict(populate_by_name=True)

    institution_aicte_id: str = Field(default="UNKNOWN")
    academic_year: str = Field(default="UNKNOWN")
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    rows_total: int = Field(default=0, ge=0)
    null_rate_per_column: Dict[str, float] = Field(default_factory=dict)
    duplicate_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    nri_share: float = Field(default=0.0, ge=0.0, le=1.0)
    oci_share: float = Field(default=0.0, ge=0.0, le=1.0)
    fn_share: float = Field(default=0.0, ge=0.0, le=1.0)
    supernumerary_share: float = Field(default=0.0, ge=0.0, le=1.0)
    intake_fill_ratio: float = Field(default=0.0, ge=0.0)

    def merge(self, other: BatchMetricState) -> BatchMetricState:
        """Merge another BatchMetricState using exact weighted aggregation."""
        total_rows = self.rows_total + other.rows_total
        if total_rows == 0:
            return self.model_copy()

        w1 = self.rows_total / total_rows
        w2 = other.rows_total / total_rows

        # Merge null rates across all unioned columns
        all_cols = set(self.null_rate_per_column.keys()).union(other.null_rate_per_column.keys())
        merged_nulls: Dict[str, float] = {}
        for col in all_cols:
            nr1 = self.null_rate_per_column.get(col, 1.0)
            nr2 = other.null_rate_per_column.get(col, 1.0)
            merged_nulls[col] = round(w1 * nr1 + w2 * nr2, 4)

        return BatchMetricState(
            institution_aicte_id=self.institution_aicte_id,
            academic_year=self.academic_year,
            batch_id=f"merged-{self.batch_id[:6]}-{other.batch_id[:6]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rows_total=total_rows,
            null_rate_per_column=merged_nulls,
            duplicate_rate=round(w1 * self.duplicate_rate + w2 * other.duplicate_rate, 4),
            nri_share=round(w1 * self.nri_share + w2 * other.nri_share, 4),
            oci_share=round(w1 * self.oci_share + w2 * other.oci_share, 4),
            fn_share=round(w1 * self.fn_share + w2 * other.fn_share, 4),
            supernumerary_share=round(
                w1 * self.supernumerary_share + w2 * other.supernumerary_share, 4
            ),
            intake_fill_ratio=round(w1 * self.intake_fill_ratio + w2 * other.intake_fill_ratio, 4),
        )

    def to_json(self) -> str:
        """Serialize state to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> BatchMetricState:
        """Deserialize state from JSON string."""
        return cls.model_validate_json(json_str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BatchMetricState:
        """Create state from dictionary."""
        return cls.model_validate(data)


def compute_batch_metric_state(
    df: pd.DataFrame,
    intake_df: Optional[pd.DataFrame] = None,
    batch_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    academic_year: Optional[str] = None,
) -> BatchMetricState:
    """Compute per-batch metric state from student records DataFrame."""
    if df.empty:
        return BatchMetricState(
            institution_aicte_id=institution_id or "UNKNOWN",
            academic_year=academic_year or "UNKNOWN",
            batch_id=batch_id or str(uuid4()),
            rows_total=0,
        )

    total_rows = len(df)

    inst = institution_id or (
        str(df["institution_aicte_id"].iloc[0]).strip()
        if "institution_aicte_id" in df.columns
        else "UNKNOWN"
    )
    acad_yr = academic_year or (
        str(df["academic_year"].iloc[0]).strip() if "academic_year" in df.columns else "UNKNOWN"
    )

    # 1. Null rate per column (excluding internal columns)
    null_rates: Dict[str, float] = {}
    for col in df.columns:
        if col.startswith("_"):
            continue
        series = df[col].fillna("").astype(str).str.strip()
        if col == "quota":
            missing_count = int(((series == "") | (df[col].isna())).sum())
        else:
            missing_count = int(
                (
                    (series == "") | (series.str.lower().isin(["nan", "null"])) | (df[col].isna())
                ).sum()
            )
        null_rates[col] = round(missing_count / total_rows, 4)

    # 2. Duplicate rate (apaar_id duplication within batch)
    if "apaar_id" in df.columns:
        apaar_clean = df["apaar_id"].fillna("").astype(str).str.strip()
        valid_apaars = apaar_clean[apaar_clean != ""]
        dup_count = int(valid_apaars.duplicated(keep=False).sum())
        dup_rate = round(dup_count / total_rows, 4)
    else:
        dup_rate = 0.0

    # 3. Quota / Nationality shares
    # NRI share
    nri_count = 0
    if "quota" in df.columns or "nri_status" in df.columns:
        quota_s = (
            df["quota"].fillna("").astype(str).str.strip().str.upper()
            if "quota" in df.columns
            else pd.Series([""] * total_rows)
        )
        nri_status_s = (
            df["nri_status"].fillna("").astype(str).str.strip().str.lower()
            if "nri_status" in df.columns
            else pd.Series([""] * total_rows)
        )
        is_nri = (quota_s == "NRI") | (nri_status_s.isin(["true", "1", "yes"]))
        nri_count = int(is_nri.sum())
    nri_share = round(nri_count / total_rows, 4)

    # OCI share
    oci_count = 0
    if "quota" in df.columns or "oci_status" in df.columns:
        quota_s = (
            df["quota"].fillna("").astype(str).str.strip().str.upper()
            if "quota" in df.columns
            else pd.Series([""] * total_rows)
        )
        oci_status_s = (
            df["oci_status"].fillna("").astype(str).str.strip().str.lower()
            if "oci_status" in df.columns
            else pd.Series([""] * total_rows)
        )
        is_oci = (quota_s == "OCI") | (oci_status_s.isin(["true", "1", "yes"]))
        oci_count = int(is_oci.sum())
    oci_share = round(oci_count / total_rows, 4)

    # FN share
    fn_count = 0
    if "quota" in df.columns or "fn_status" in df.columns:
        quota_s = (
            df["quota"].fillna("").astype(str).str.strip().str.upper()
            if "quota" in df.columns
            else pd.Series([""] * total_rows)
        )
        fn_status_s = (
            df["fn_status"].fillna("").astype(str).str.strip().str.lower()
            if "fn_status" in df.columns
            else pd.Series([""] * total_rows)
        )
        is_fn = (quota_s == "FN") | (fn_status_s.isin(["true", "1", "yes"]))
        fn_count = int(is_fn.sum())
    fn_share = round(fn_count / total_rows, 4)

    # 4. Supernumerary share
    supernumerary_count = 0
    if "seat_type" in df.columns:
        seats = df["seat_type"].fillna("").astype(str).str.strip().str.upper()
        supernumerary_count = int((seats == "SUPERNUMERARY").sum())
    supernumerary_share = round(supernumerary_count / total_rows, 4)

    # 5. Intake fill ratio
    fill_ratio = 0.0
    if intake_df is not None and not intake_df.empty:
        # Match intake for this institution
        matching_intake = intake_df
        if "institution_aicte_id" in intake_df.columns and inst != "UNKNOWN":
            matching_intake = intake_df[
                intake_df["institution_aicte_id"].astype(str).str.strip() == inst
            ]
        if not matching_intake.empty and "approved_intake" in matching_intake.columns:
            total_approved = int(matching_intake["approved_intake"].sum())
            if total_approved > 0:
                regular_enrolled = total_rows - supernumerary_count
                fill_ratio = round(regular_enrolled / total_approved, 4)

    return BatchMetricState(
        institution_aicte_id=inst,
        academic_year=acad_yr,
        batch_id=batch_id or str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        rows_total=total_rows,
        null_rate_per_column=null_rates,
        duplicate_rate=dup_rate,
        nri_share=nri_share,
        oci_share=oci_share,
        fn_share=fn_share,
        supernumerary_share=supernumerary_share,
        intake_fill_ratio=fill_ratio,
    )
