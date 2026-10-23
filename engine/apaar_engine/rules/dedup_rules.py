"""engine/apaar_engine/rules/dedup_rules.py

Rule registrations for duplicate detection and metric anomalies:
- V009: Probable duplicate person in batch under different APAAR (fuzzy name + DOB)
- V010: Same APAAR ACTIVE at another institution in the same academic year
- V011: Probable same person at another institution under different APAAR (Splink)
- V020: Batch metric anomaly vs institution history

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from apaar_engine.anomaly.detect import detect_batch_anomalies
from apaar_engine.anomaly.metrics import BatchMetricState, compute_batch_metric_state
from apaar_engine.dedup.cross import detect_cross_duplicates
from apaar_engine.dedup.intra import detect_intra_duplicates
from apaar_engine.models import Issue
from apaar_engine.rules.registry import register_rule


@register_rule("V009")
def validate_v009_intra_dedup(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    **kwargs: Any,
) -> List[Issue]:
    """V009: Probable duplicate person in the batch with a different APAAR."""
    params = rule_meta.get("params", {})
    flag_threshold = params.get("flag_threshold", 0.92)
    review_threshold = params.get("review_threshold", 0.75)

    issues, clusters = detect_intra_duplicates(
        df,
        flag_threshold=flag_threshold,
        review_threshold=review_threshold,
    )
    # If caller provided an accumulator for duplicate clusters
    collector = kwargs.get("cluster_collector")
    if collector is not None and isinstance(collector, list):
        collector.extend(clusters)

    return issues


@register_rule("V010")
def validate_v010_cross_active(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    central_df: Any = None,
    history: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V010: Same APAAR ACTIVE at another institution in the same academic year."""
    ref_df = (
        central_df
        if central_df is not None
        else (history if isinstance(history, pd.DataFrame) else None)
    )
    if ref_df is None:
        return []

    issues, clusters = detect_cross_duplicates(df, ref_df)
    v010_issues = [iss for iss in issues if iss.rule_id == "V010"]
    v010_clusters = [cl for cl in clusters if cl.evidence and cl.evidence.get("rule_id") == "V010"]

    collector = kwargs.get("cluster_collector")
    if collector is not None and isinstance(collector, list):
        collector.extend(v010_clusters)

    return v010_issues


@register_rule("V011")
def validate_v011_cross_fuzzy(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    central_df: Any = None,
    history: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V011: Probable same person at another institution under a different APAAR."""
    ref_df = (
        central_df
        if central_df is not None
        else (history if isinstance(history, pd.DataFrame) else None)
    )
    if ref_df is None:
        return []

    params = rule_meta.get("params", {})
    flag_threshold = params.get("flag_threshold", 0.92)
    review_threshold = params.get("review_threshold", 0.75)

    issues, clusters = detect_cross_duplicates(
        df,
        ref_df,
        flag_threshold=flag_threshold,
        review_threshold=review_threshold,
    )
    v011_issues = [iss for iss in issues if iss.rule_id == "V011"]
    v011_clusters = [cl for cl in clusters if cl.evidence and cl.evidence.get("rule_id") == "V011"]

    collector = kwargs.get("cluster_collector")
    if collector is not None and isinstance(collector, list):
        collector.extend(v011_clusters)

    return v011_issues


@register_rule("V020")
def validate_v020_batch_metric_anomaly(
    df: pd.DataFrame,
    rule_meta: Dict[str, Any],
    history: Any = None,
    intake_df: Any = None,
    peer_history: Any = None,
    **kwargs: Any,
) -> List[Issue]:
    """V020: Batch metric anomaly vs. institution history."""
    if history is None and peer_history is None:
        return []

    # Parse history states
    hist_states: List[BatchMetricState] = []
    if history is not None:
        if isinstance(history, list):
            for h in history:
                if isinstance(h, BatchMetricState):
                    hist_states.append(h)
                elif isinstance(h, dict):
                    hist_states.append(BatchMetricState.from_dict(h))
                elif isinstance(h, pd.DataFrame):
                    hist_states.append(compute_batch_metric_state(h, intake_df=intake_df))
        elif isinstance(history, pd.DataFrame):
            hist_states.append(compute_batch_metric_state(history, intake_df=intake_df))

    peer_states: List[BatchMetricState] = []
    if peer_history is not None and isinstance(peer_history, list):
        for p in peer_history:
            if isinstance(p, BatchMetricState):
                peer_states.append(p)
            elif isinstance(p, dict):
                peer_states.append(BatchMetricState.from_dict(p))

    current_state = compute_batch_metric_state(df, intake_df=intake_df)

    params = rule_meta.get("params", {})
    z_threshold = params.get("z_score_threshold", 3.0)
    min_batches = params.get("min_historical_batches", 3)

    issues, anomalies = detect_batch_anomalies(
        current_metrics=current_state,
        history=hist_states if hist_states else None,
        peer_metrics=peer_states if peer_states else None,
        z_threshold=z_threshold,
        min_historical_batches=min_batches,
    )

    collector = kwargs.get("anomaly_collector")
    if collector is not None and isinstance(collector, list):
        collector.extend(anomalies)

    return issues
