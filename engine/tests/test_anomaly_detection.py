"""engine/tests/test_anomaly_detection.py

Unit and integration tests for Deequ-style batch metric states and anomaly detection (V020).
Owned by Team A (Data & Intelligence).
"""

import pandas as pd

from apaar_engine.anomaly.detect import detect_batch_anomalies
from apaar_engine.anomaly.metrics import BatchMetricState, compute_batch_metric_state
from apaar_engine.models import Severity


def test_batch_metric_state_computation_and_merge():
    data1 = [
        {"full_name": "A", "apaar_id": "1111", "quota": "NRI", "seat_type": "REGULAR"},
        {"full_name": "B", "apaar_id": "2222", "quota": "NONE", "seat_type": "REGULAR"},
    ]
    df1 = pd.DataFrame(data1)
    state1 = compute_batch_metric_state(df1, batch_id="b1", institution_id="1-10001")
    assert state1.rows_total == 2
    assert state1.nri_share == 0.5
    assert state1.duplicate_rate == 0.0

    # Serialization roundtrip
    json_str = state1.to_json()
    deserialized = BatchMetricState.from_json(json_str)
    assert deserialized.rows_total == state1.rows_total
    assert deserialized.nri_share == state1.nri_share

    # Merge states
    data2 = [
        {"full_name": "C", "apaar_id": "3333", "quota": "NONE", "seat_type": "SUPERNUMERARY"},
        {"full_name": "D", "apaar_id": "4444", "quota": "NONE", "seat_type": "SUPERNUMERARY"},
    ]
    df2 = pd.DataFrame(data2)
    state2 = compute_batch_metric_state(df2, batch_id="b2", institution_id="1-10001")

    merged = state1.merge(state2)
    assert merged.rows_total == 4
    # Weighted average: (0.5 * 2 + 0.0 * 2) / 4 = 0.25
    assert merged.nri_share == 0.25
    # Supernumerary: (0.0 * 2 + 1.0 * 2) / 4 = 0.50
    assert merged.supernumerary_share == 0.5


def test_v020_z_score_historical_anomaly():
    # 3 historical batches with NRI share around 2%
    history = [
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.020),
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.022),
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.019),
    ]

    # Current batch with sudden spike to 35% NRI
    current = BatchMetricState(
        institution_aicte_id="1-10001",
        rows_total=200,
        nri_share=0.35,
    )

    issues, anomalies = detect_batch_anomalies(current, history=history)

    assert len(anomalies) >= 1
    nri_anomalies = [a for a in anomalies if a.metric == "nri_share"]
    assert len(nri_anomalies) == 1
    assert nri_anomalies[0].value == 0.35
    assert nri_anomalies[0].baseline < 0.03
    assert nri_anomalies[0].z >= 3.0
    assert "jump in NRI / international quota share" in nri_anomalies[0].reason

    assert len(issues) >= 1
    assert issues[0].rule_id == "V020"
    assert issues[0].severity == Severity.WARN


def test_v020_fallback_to_peer_group():
    # No institution history (< 3 batches), but peer group available
    peers = [
        BatchMetricState(institution_aicte_id="1-10002", rows_total=200, supernumerary_share=0.03),
        BatchMetricState(institution_aicte_id="1-10003", rows_total=200, supernumerary_share=0.035),
    ]

    # Current batch with extreme supernumerary share = 40%
    current = BatchMetricState(
        institution_aicte_id="1-10001",
        rows_total=200,
        supernumerary_share=0.40,
    )

    issues, anomalies = detect_batch_anomalies(current, history=None, peer_metrics=peers)

    super_anom = [a for a in anomalies if a.metric == "supernumerary_share"]
    assert len(super_anom) == 1
    assert super_anom[0].value == 0.40
    assert "peer group average" in super_anom[0].reason
