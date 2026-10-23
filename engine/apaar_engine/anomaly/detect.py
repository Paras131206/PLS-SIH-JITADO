"""engine/apaar_engine/anomaly/detect.py

V020: Anomaly detection on batch metrics.
- Computes z-score and relative change against institution's history (min 3 batches).
- Falls back to peer-group baseline by state/program when history < 3 batches.
- Runs IsolationForest across institutions for multivariate outlier detection.
- Generates human-readable explanations for every flagged anomaly.

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest

from apaar_engine.anomaly.metrics import BatchMetricState
from apaar_engine.models import Anomaly, Issue, Severity

METRIC_LABELS = {
    "nri_share": "NRI / international quota share",
    "supernumerary_share": "supernumerary seat enrolment share",
    "intake_fill_ratio": "approved intake fill ratio",
    "duplicate_rate": "duplicate APAAR collision rate",
    "avg_null_rate": "average missing field rate",
}


def _extract_metric_val(state: BatchMetricState, metric_key: str) -> float:
    """Extract numeric value for a named metric from a BatchMetricState."""
    if metric_key == "avg_null_rate":
        nulls = state.null_rate_per_column.values()
        return sum(nulls) / len(nulls) if nulls else 0.0
    return float(getattr(state, metric_key, 0.0))


def detect_batch_anomalies(
    current_metrics: BatchMetricState,
    history: Optional[List[BatchMetricState]] = None,
    peer_metrics: Optional[List[BatchMetricState]] = None,
    z_threshold: float = 3.0,
    min_historical_batches: int = 3,
) -> Tuple[List[Issue], List[Anomaly]]:
    """Detect statistical and multivariate anomalies in batch metrics (V020).

    Args:
        current_metrics: Metric state of the batch under validation.
        history: Prior metric states from the same institution.
        peer_metrics: Metric states from peer institutions.
        z_threshold: Z-score cutoff for univariate anomalies (default 3.0).
        min_historical_batches: Minimum historical batches required (default 3).

    Returns:
        tuple of (issues, anomalies).
    """
    issues: List[Issue] = []
    anomalies: List[Anomaly] = []

    metrics_to_check = [
        "nri_share",
        "supernumerary_share",
        "intake_fill_ratio",
        "duplicate_rate",
        "avg_null_rate",
    ]

    # -----------------------------------------------------------------------
    # 1. Univariate Z-Score / Relative Change Detection
    # -----------------------------------------------------------------------
    has_sufficient_history = history is not None and len(history) >= min_historical_batches

    reference_states = history if has_sufficient_history else peer_metrics
    reference_type = "historical" if has_sufficient_history else "peer group"

    if reference_states and len(reference_states) >= 1:
        for m_key in metrics_to_check:
            curr_val = _extract_metric_val(current_metrics, m_key)
            ref_vals = [_extract_metric_val(st, m_key) for st in reference_states]

            mean_val = sum(ref_vals) / len(ref_vals)
            variance = sum((x - mean_val) ** 2 for x in ref_vals) / len(ref_vals)
            std_val = math.sqrt(variance)

            # Calculate z-score
            if std_val > 0.001:
                z = abs(curr_val - mean_val) / std_val
            else:
                # Low historical variance: calculate relative jump if delta is notable
                delta = abs(curr_val - mean_val)
                z = (delta / (mean_val + 0.01)) * 3.0 if delta >= 0.05 else 0.0

            label = METRIC_LABELS.get(m_key, m_key)

            if z >= z_threshold and abs(curr_val - mean_val) >= 0.05:
                direction = "jump" if curr_val > mean_val else "drop"
                reason = (
                    f"Sudden {direction} in {label}: current {curr_val:.1%} vs "
                    f"{reference_type} average {mean_val:.1%} (z-score: {z:.2f})"
                )
                anomalies.append(
                    Anomaly(
                        metric=m_key,
                        value=round(curr_val, 4),
                        baseline=round(mean_val, 4),
                        z=round(z, 2),
                        reason=reason,
                    )
                )
                issues.append(
                    Issue(
                        row=None,
                        field=m_key,
                        rule_id="V020",
                        severity=Severity.WARN,
                        message=reason,
                    )
                )

    # -----------------------------------------------------------------------
    # 2. Multivariate IsolationForest Across Institutions
    # -----------------------------------------------------------------------
    all_peers = list(peer_metrics) if peer_metrics else []
    if history:
        all_peers.extend(history)

    if len(all_peers) >= 5:
        feature_keys = [
            "nri_share",
            "supernumerary_share",
            "intake_fill_ratio",
            "duplicate_rate",
            "avg_null_rate",
        ]

        X_ref = np.array([[_extract_metric_val(st, k) for k in feature_keys] for st in all_peers])
        X_curr = np.array([[_extract_metric_val(current_metrics, k) for k in feature_keys]])

        try:
            iso_forest = IsolationForest(
                contamination=0.05,
                random_state=42,
                n_estimators=100,
            )
            iso_forest.fit(X_ref)
            prediction = iso_forest.predict(X_curr)[0]

            if prediction == -1:
                # Identified as multivariate outlier
                # Find the feature with highest deviation from peer median
                medians = np.median(X_ref, axis=0)
                stds = np.std(X_ref, axis=0) + 1e-4
                deviations = np.abs(X_curr[0] - medians) / stds
                max_dev_idx = int(np.argmax(deviations))
                top_feature = feature_keys[max_dev_idx]
                top_label = METRIC_LABELS.get(top_feature, top_feature)

                reason = (
                    f"Multivariate outlier across institutions via IsolationForest "
                    f"(extreme deviation in {top_label}: "
                    f"{X_curr[0][max_dev_idx]:.1%} vs median {medians[max_dev_idx]:.1%})"
                )

                # Avoid duplicate anomaly if metric was already flagged above
                if not any(a.metric == top_feature for a in anomalies):
                    anomalies.append(
                        Anomaly(
                            metric="multivariate_distribution",
                            value=round(float(X_curr[0][max_dev_idx]), 4),
                            baseline=round(float(medians[max_dev_idx]), 4),
                            z=round(float(deviations[max_dev_idx]), 2),
                            reason=reason,
                        )
                    )
                    issues.append(
                        Issue(
                            row=None,
                            field="metrics",
                            rule_id="V020",
                            severity=Severity.WARN,
                            message=reason,
                        )
                    )
        except Exception:
            pass

    return issues, anomalies
