"""engine/apaar_engine/anomaly package.

Deequ-style per-batch metric states and historical/cross-institution anomaly detection (V020).

Owned by Team A (Data & Intelligence).
"""

from apaar_engine.anomaly.metrics import BatchMetricState, compute_batch_metric_state

__all__ = [
    "BatchMetricState",
    "compute_batch_metric_state",
]
