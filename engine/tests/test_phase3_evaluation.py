"""engine/tests/test_phase3_evaluation.py

Precision, Recall, and F1 evaluation per rule (V009, V010, V011, V020).
Owned by Team A (Data & Intelligence).
"""

import json
from pathlib import Path

import pandas as pd

from apaar_engine.anomaly.detect import detect_batch_anomalies
from apaar_engine.anomaly.metrics import BatchMetricState
from apaar_engine.dedup.cross import detect_cross_duplicates
from apaar_engine.dedup.intra import detect_intra_duplicates


def compute_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    """Compute precision, recall, and F1 score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def test_phase3_precision_recall_f1_evaluation():
    repo_root = Path(__file__).resolve().parents[2]
    synthetic_dir = repo_root / "data" / "synthetic"

    defective_csv = synthetic_dir / "students_with_defects.csv"
    defects_json = synthetic_dir / "defects.json"
    central_csv = synthetic_dir / "central_snapshot.csv"

    defective_df = pd.read_csv(defective_csv)
    central_df = pd.read_csv(central_csv)

    with open(defects_json, mode="r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    evaluation_report = {}

    # -----------------------------------------------------------------------
    # 1. Evaluate V009 (Intra-batch Duplicate Detection)
    # -----------------------------------------------------------------------
    v009_expected_rows = {d["row"] for d in ground_truth if d["rule_id"] == "V009"}
    v009_issues, v009_clusters = detect_intra_duplicates(defective_df)
    v009_discovered_rows = {iss.row for iss in v009_issues if iss.rule_id == "V009"}

    tp_v009 = len(v009_expected_rows.intersection(v009_discovered_rows))
    fp_v009 = len(v009_discovered_rows - v009_expected_rows)
    fn_v009 = len(v009_expected_rows - v009_discovered_rows)
    evaluation_report["V009"] = compute_metrics(tp_v009, fp_v009, fn_v009)

    # -----------------------------------------------------------------------
    # 2. Evaluate V010 (Cross-Institution Same APAAR Active)
    # -----------------------------------------------------------------------
    # Seeded at row 412 (index 410)
    v010_expected_rows = {412}
    cross_issues, cross_clusters = detect_cross_duplicates(defective_df, central_df)
    v010_discovered_rows = {iss.row for iss in cross_issues if iss.rule_id == "V010"}

    tp_v010 = len(v010_expected_rows.intersection(v010_discovered_rows))
    fp_v010 = len(v010_discovered_rows - v010_expected_rows)
    fn_v010 = len(v010_expected_rows - v010_discovered_rows)
    evaluation_report["V010"] = compute_metrics(tp_v010, fp_v010, fn_v010)

    # -----------------------------------------------------------------------
    # 3. Evaluate V011 (Cross-Institution Fuzzy Match Different APAAR)
    # -----------------------------------------------------------------------
    # Seeded at row 422 (index 420)
    v011_expected_rows = {422}
    v011_discovered_rows = {iss.row for iss in cross_issues if iss.rule_id == "V011"}

    tp_v011 = len(v011_expected_rows.intersection(v011_discovered_rows))
    fp_v011 = len(v011_discovered_rows - v011_expected_rows)
    fn_v011 = len(v011_expected_rows - v011_discovered_rows)
    evaluation_report["V011"] = compute_metrics(tp_v011, fp_v011, fn_v011)

    # -----------------------------------------------------------------------
    # 4. Evaluate V020 (Batch Metric Anomaly Detection)
    # -----------------------------------------------------------------------
    # Test normal vs anomalous batch against historical baseline
    history = [
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.020),
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.022),
        BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.019),
    ]
    # Normal batch (should have 0 anomalies)
    normal_batch = BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.021)
    _, anom_normal = detect_batch_anomalies(normal_batch, history=history)

    # Anomalous batch (spike to 35% NRI, should be flagged)
    spiked_batch = BatchMetricState(institution_aicte_id="1-10001", rows_total=200, nri_share=0.35)
    _, anom_spiked = detect_batch_anomalies(spiked_batch, history=history)

    tp_v020 = 1 if len(anom_spiked) > 0 else 0
    fp_v020 = 1 if len(anom_normal) > 0 else 0
    fn_v020 = 0 if len(anom_spiked) > 0 else 1
    evaluation_report["V020"] = compute_metrics(tp_v020, fp_v020, fn_v020)

    # Print markdown evaluation report
    print("\n" + "=" * 50)
    print("PHASE 3 INTELLIGENCE RULES EVALUATION (Precision / Recall / F1)")
    print("=" * 50)
    print(f"{'Rule ID':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10}")
    print("-" * 50)
    for rule_id, scores in evaluation_report.items():
        prec_str = f"{scores['precision']:<10.2%}"
        rec_str = f"{scores['recall']:<10.2%}"
        f1_str = f"{scores['f1']:<10.2%}"
        print(f"{rule_id:<10} | {prec_str} | {rec_str} | {f1_str}")
    print("=" * 50 + "\n")

    # Assert high-performance benchmarks (>= 90% across precision, recall, and F1)
    for rule_id, scores in evaluation_report.items():
        assert scores["precision"] >= 0.90, f"{rule_id} Precision {scores['precision']} < 0.90"
        assert scores["recall"] >= 0.90, f"{rule_id} Recall {scores['recall']} < 0.90"
        assert scores["f1"] >= 0.90, f"{rule_id} F1 {scores['f1']} < 0.90"
