"""engine/apaar_engine/dedup/cross.py

Cross-institution duplicate detection:
- V010: Same APAAR ACTIVE at another institution in the same academic year (exact match).
- V011: Probable same person at another institution under a different APAAR
  using Splink (DuckDB backend, link_only mode).

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pandas as pd

from apaar_engine.dedup.intra import score_pair
from apaar_engine.dedup.normalize import normalize_indian_name
from apaar_engine.models import DuplicateCluster, DuplicateScope, Issue, Severity, mask_apaar

logger = logging.getLogger(__name__)


def detect_cross_duplicates(
    batch_df: pd.DataFrame,
    central_df: Optional[pd.DataFrame],
    flag_threshold: float = 0.92,
    review_threshold: float = 0.75,
) -> Tuple[List[Issue], List[DuplicateCluster]]:
    """Detect cross-institution duplicate enrolments (V010 and V011).

    Args:
        batch_df: Newly uploaded batch records.
        central_df: Central repository snapshot of existing institution records.
        flag_threshold: Score threshold for flagging warnings (default 0.92).
        review_threshold: Score threshold for analyst review queue (default 0.75).

    Returns:
        tuple of (issues, duplicate_clusters).
    """
    issues: List[Issue] = []
    clusters: List[DuplicateCluster] = []

    if central_df is None or central_df.empty or batch_df.empty:
        return issues, clusters

    # -----------------------------------------------------------------------
    # V010: Same APAAR ACTIVE at another institution in same academic year
    # -----------------------------------------------------------------------
    v010_issues, v010_clusters = _detect_v010_active_apaar(batch_df, central_df)
    issues.extend(v010_issues)
    clusters.extend(v010_clusters)

    # -----------------------------------------------------------------------
    # V011: Probable same person at another institution under different APAAR
    # using Splink (DuckDB, link_only)
    # -----------------------------------------------------------------------
    v011_issues, v011_clusters = _detect_v011_splink_fuzzy(
        batch_df,
        central_df,
        flag_threshold=flag_threshold,
        review_threshold=review_threshold,
    )
    issues.extend(v011_issues)
    clusters.extend(v011_clusters)

    return issues, clusters


def _detect_v010_active_apaar(
    batch_df: pd.DataFrame,
    central_df: pd.DataFrame,
) -> Tuple[List[Issue], List[DuplicateCluster]]:
    """V010 check: Exact same APAAR active at another institution in the same year."""
    issues: List[Issue] = []
    clusters: List[DuplicateCluster] = []

    required = ["apaar_id", "institution_aicte_id", "academic_year", "enrolment_status"]
    if not all(c in batch_df.columns for c in required) or not all(
        c in central_df.columns for c in required
    ):
        return issues, clusters

    # Filter central to active enrolments
    central_active = central_df[
        central_df["enrolment_status"].fillna("").astype(str).str.strip().str.upper() == "ACTIVE"
    ].copy()

    if central_active.empty:
        return issues, clusters

    row_nums = (
        batch_df["_row_num"].tolist()
        if "_row_num" in batch_df.columns
        else [idx + 2 for idx in range(len(batch_df))]
    )

    batch_apaars = batch_df["apaar_id"].fillna("").astype(str).str.strip().tolist()
    batch_insts = batch_df["institution_aicte_id"].fillna("").astype(str).str.strip().tolist()
    batch_years = batch_df["academic_year"].fillna("").astype(str).str.strip().tolist()
    batch_statuses = (
        batch_df["enrolment_status"].fillna("").astype(str).str.strip().str.upper().tolist()
    )

    # Pre-index central_active by apaar_id
    central_by_apaar: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in central_active.iterrows():
        ap = str(row.get("apaar_id", "")).strip()
        if ap and len(ap) == 12:
            central_by_apaar.setdefault(ap, []).append(
                {
                    "institution_aicte_id": str(row.get("institution_aicte_id", "")).strip(),
                    "academic_year": str(row.get("academic_year", "")).strip(),
                    "enrolment_status": str(row.get("enrolment_status", "")).strip(),
                    "full_name": str(row.get("full_name", "")).strip(),
                }
            )

    flagged_rows = set()

    for idx, (r_num, ap, inst, year, status) in enumerate(
        zip(row_nums, batch_apaars, batch_insts, batch_years, batch_statuses)
    ):
        if status != "ACTIVE" or len(ap) != 12 or not ap.isdigit():
            continue

        if ap in central_by_apaar:
            for central_rec in central_by_apaar[ap]:
                other_inst = central_rec["institution_aicte_id"]
                other_year = central_rec["academic_year"]

                if other_inst != inst and other_year == year:
                    cluster_id = f"cross-v010-{uuid4().hex[:8]}"
                    clusters.append(
                        DuplicateCluster(
                            cluster_id=cluster_id,
                            apaar_ids=[ap],
                            score=1.0,
                            scope=DuplicateScope.CROSS_INSTITUTION,
                            evidence={
                                "rule_id": "V010",
                                "apaar_id": mask_apaar(ap),
                                "row": r_num,
                                "batch_institution": inst,
                                "central_institution": other_inst,
                                "academic_year": year,
                                "enrolment_status": "ACTIVE",
                            },
                        )
                    )

                    if r_num not in flagged_rows:
                        flagged_rows.add(r_num)
                        issues.append(
                            Issue(
                                row=r_num,
                                field="apaar_id",
                                rule_id="V010",
                                severity=Severity.ERROR,
                                message=(
                                    f"Same APAAR '{mask_apaar(ap)}' is ACTIVE at another "
                                    f"institution '{other_inst}' in academic year '{year}'"
                                ),
                                value_masked=mask_apaar(ap),
                            )
                        )

    return issues, clusters


def _detect_v011_splink_fuzzy(
    batch_df: pd.DataFrame,
    central_df: pd.DataFrame,
    flag_threshold: float = 0.92,
    review_threshold: float = 0.75,
) -> Tuple[List[Issue], List[DuplicateCluster]]:
    """V011 check: Splink (DuckDB, link_only) fuzzy match with a different APAAR."""
    issues: List[Issue] = []
    clusters: List[DuplicateCluster] = []

    required = ["apaar_id", "full_name", "dob", "gender", "institution_aicte_id"]
    if not all(c in batch_df.columns for c in required) or not all(
        c in central_df.columns for c in required
    ):
        return issues, clusters

    try:
        # pyrefly: ignore[missing-import]
        import splink.comparison_library as cl

        # pyrefly: ignore[missing-import]
        from splink import DuckDBAPI, Linker, SettingsCreator, block_on
    except ImportError as e:
        logger.warning("Splink / DuckDB not available for V011 cross-dedup: %s", e)
        return issues, clusters

    row_nums = (
        batch_df["_row_num"].tolist()
        if "_row_num" in batch_df.columns
        else [idx + 2 for idx in range(len(batch_df))]
    )

    # Prepare batch dataframe
    batch_clean = pd.DataFrame(
        {
            "unique_id": [f"batch_{r}" for r in row_nums],
            "apaar_id": batch_df["apaar_id"].fillna("").astype(str).str.strip(),
            "name": batch_df["full_name"].fillna("").astype(str).apply(normalize_indian_name),
            "dob": batch_df["dob"].fillna("").astype(str).str.strip(),
            "gender": batch_df["gender"].fillna("").astype(str).str.strip().str.upper(),
            "institution_aicte_id": batch_df["institution_aicte_id"]
            .fillna("")
            .astype(str)
            .str.strip(),
        }
    )

    # Prepare central dataframe
    central_clean = pd.DataFrame(
        {
            "unique_id": [f"central_{i}" for i in range(len(central_df))],
            "apaar_id": central_df["apaar_id"].fillna("").astype(str).str.strip(),
            "name": central_df["full_name"].fillna("").astype(str).apply(normalize_indian_name),
            "dob": central_df["dob"].fillna("").astype(str).str.strip(),
            "gender": central_df["gender"].fillna("").astype(str).str.strip().str.upper(),
            "institution_aicte_id": central_df["institution_aicte_id"]
            .fillna("")
            .astype(str)
            .str.strip(),
        }
    )

    # Filter out empty names / dobs
    batch_clean = batch_clean[(batch_clean["name"] != "") & (batch_clean["dob"] != "")]
    central_clean = central_clean[(central_clean["name"] != "") & (central_clean["dob"] != "")]

    if batch_clean.empty or central_clean.empty:
        return issues, clusters

    batch_clean_map = {row["unique_id"]: row.to_dict() for _, row in batch_clean.iterrows()}
    central_clean_map = {row["unique_id"]: row.to_dict() for _, row in central_clean.iterrows()}

    settings = SettingsCreator(
        link_type="link_only",
        comparisons=[
            cl.ExactMatch("dob"),
            cl.ExactMatch("gender"),
            cl.JaroWinklerAtThresholds("name", [0.85]),
        ],
        blocking_rules_to_generate_predictions=[
            block_on("dob", "gender"),
        ],
        additional_columns_to_retain=["apaar_id", "institution_aicte_id"],
    )

    try:
        db_api = DuckDBAPI()
        table_l = db_api.register(batch_clean)
        table_r = db_api.register(central_clean)
        linker = Linker([table_l, table_r], settings, log_level=40)
        df_predict = linker.inference.predict(threshold_match_probability=review_threshold)
        pred_pd = df_predict.as_pandas_dataframe()
    except Exception as exc:
        logger.warning("Splink prediction failed: %s", exc)
        return issues, clusters

    if pred_pd.empty:
        return issues, clusters

    flagged_rows = set()

    for _, row in pred_pd.iterrows():
        uid_l = str(row.get("unique_id_l", ""))
        uid_r = str(row.get("unique_id_r", ""))

        b_rec = batch_clean_map.get(uid_l, {})
        c_rec = central_clean_map.get(uid_r, {})

        apaar_l = str(b_rec.get("apaar_id", "")).strip()
        apaar_r = str(c_rec.get("apaar_id", "")).strip()
        inst_l = str(b_rec.get("institution_aicte_id", "")).strip()
        inst_r = str(c_rec.get("institution_aicte_id", "")).strip()
        name_l = str(b_rec.get("name", "")).strip()
        name_r = str(c_rec.get("name", "")).strip()
        dob_l = str(b_rec.get("dob", "")).strip()
        dob_r = str(c_rec.get("dob", "")).strip()
        orig_row = int(uid_l.replace("batch_", "")) if "batch_" in uid_l else 0

        # Must be different APAAR and different institution
        if apaar_l == apaar_r or inst_l == inst_r:
            continue

        pair_score = score_pair(name_l, name_r, dob_l, dob_r)
        if pair_score < review_threshold:
            continue

        score_val = round(pair_score, 4)
        status = "FLAG" if score_val >= flag_threshold else "REVIEW"
        cluster_id = f"cross-v011-{uuid4().hex[:8]}"
        cluster = DuplicateCluster(
            cluster_id=cluster_id,
            apaar_ids=[apaar_l, apaar_r],
            score=score_val,
            scope=DuplicateScope.CROSS_INSTITUTION,
            evidence={
                "rule_id": "V011",
                "status": status,
                "batch_row": orig_row,
                "batch_apaar": mask_apaar(apaar_l),
                "central_apaar": mask_apaar(apaar_r),
                "batch_institution": inst_l,
                "central_institution": inst_r,
                "name_batch": name_l,
                "name_central": name_r,
                "dob": dob_l,
                "score": score_val,
            },
        )
        clusters.append(cluster)

        if score_val >= flag_threshold and orig_row not in flagged_rows:
            flagged_rows.add(orig_row)
            issues.append(
                Issue(
                    row=orig_row,
                    field="full_name",
                    rule_id="V011",
                    severity=Severity.WARN,
                    message=(
                        f"Probable same person at another institution '{inst_r}' under "
                        f"different APAAR '{mask_apaar(apaar_r)}' (similarity {score_val:.2f})"
                    ),
                    value_masked=mask_apaar(apaar_l),
                )
            )

    return issues, clusters
