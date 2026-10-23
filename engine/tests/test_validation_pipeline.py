"""engine/tests/test_validation_pipeline.py

End-to-end batch validation pipeline tests:
- Clean dataset (students.csv) has zero issues and 100% quality score.
- Defective dataset (students_with_defects.csv) finds every defect from defects.json.
- Clean rows have no issues.
- Intake summary and weighted quality score metrics validated.

Owned by Team A (Data & Intelligence).
"""

import json
from pathlib import Path

import pandas as pd

from apaar_engine.registry import MockApaarRegistry
from apaar_engine.validate import validate_batch


def test_validate_clean_students_csv():
    repo_root = Path(__file__).resolve().parents[2]
    students_csv = repo_root / "data" / "synthetic" / "students.csv"
    intake_csv = repo_root / "data" / "synthetic" / "intake.csv"
    registry_csv = repo_root / "data" / "synthetic" / "registry.csv"

    intake_df = pd.read_csv(intake_csv)
    registry = MockApaarRegistry.from_csv(registry_csv)
    report = validate_batch(students_csv, intake_df=intake_df, registry=registry)

    assert report.rows_total == 1000
    assert report.rows_error == 0
    assert report.rows_warning == 0
    assert report.rows_valid == 1000
    assert report.quality_score == 100.0
    assert len(report.issues) == 0

    # Column metrics populated
    assert "completeness" in report.metrics
    assert "uniqueness" in report.metrics
    assert report.metrics["completeness"]["apaar_id"] == 1.0
    assert report.metrics["uniqueness"]["apaar_id"] == 1.0

    # Intake summaries populated
    assert len(report.intake_summary) >= 3
    for summary in report.intake_summary:
        assert summary.approved > 0
        assert summary.enrolled_regular <= summary.approved
        assert summary.excess == 0
        assert isinstance(summary.supernumerary_by_scheme, dict)


def test_validate_students_with_defects_matches_ground_truth():
    repo_root = Path(__file__).resolve().parents[2]
    defective_csv = repo_root / "data" / "synthetic" / "students_with_defects.csv"
    defects_json = repo_root / "data" / "synthetic" / "defects.json"
    intake_csv = repo_root / "data" / "synthetic" / "intake.csv"
    registry_csv = repo_root / "data" / "synthetic" / "registry.csv"

    with open(defects_json, mode="r", encoding="utf-8") as f:
        ground_truth_defects = json.load(f)

    intake_df = pd.read_csv(intake_csv)
    registry = MockApaarRegistry.from_csv(registry_csv)
    report = validate_batch(defective_csv, intake_df=intake_df, registry=registry)

    # Map discovered issues by (row, rule_id)
    discovered = {(iss.row, iss.rule_id): iss for iss in report.issues}

    # Verify that every injected defect in defects.json is discovered
    for expected in ground_truth_defects:
        key = (expected["row"], expected["rule_id"])
        assert key in discovered, (
            f"Expected defect {key} ({expected['description']}) was not found! "
            f"All discovered keys: {sorted(discovered.keys())}"
        )

    # Verify that clean rows (rows not in defects.json) have no issues
    expected_defective_rows = {d["row"] for d in ground_truth_defects}
    for iss in report.issues:
        assert iss.row in expected_defective_rows, (
            f"Clean row {iss.row} unexpectedly flagged with rule {iss.rule_id}: {iss.message}"
        )

    assert report.rows_total == 1000
    assert report.rows_error > 0
    assert report.quality_score < 100.0
