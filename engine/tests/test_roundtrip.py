"""engine/tests/test_roundtrip.py

Test that Pydantic v2 models round-trip the generated synthetic CSV data.
Owned by Team A (Data & Intelligence).
"""

import csv
import json
from pathlib import Path

from apaar_engine.models import ProgramIntake, StudentRecord


def test_roundtrip_students_csv():
    csv_path = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "students.csv"
    assert csv_path.exists(), f"students.csv not found at {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1000, f"Expected 1000 students, got {len(rows)}"

    for i, row in enumerate(rows):
        # 1. Parse row into StudentRecord Pydantic v2 model
        record = StudentRecord(**row)

        # 2. Verify key invariants
        assert len(record.apaar_id) == 12
        assert record.apaar_id.isdigit()
        assert record.apaar_masked == f"{record.apaar_id[:4]}****{record.apaar_id[8:]}"
        assert record.institution_aicte_id in [
            "1-10001",
            "1-10002",
            "1-10003",
            "1-10004",
            "1-10005",
        ]
        assert record.program_code in ["UG-CSE", "UG-ECE", "UG-MECH"]
        assert record.academic_year == "2026-27"
        assert record.course_level.value == "UG"

        # 3. Round-trip to JSON and re-parse
        json_data = record.model_dump_json()
        record_reconstructed = StudentRecord.model_validate_json(json_data)
        assert record == record_reconstructed

        # 4. Check round-trip back to serialized dict
        dumped = record.model_dump(mode="json")
        assert dumped["apaar_id"] == row["apaar_id"]
        assert dumped["dob"] == row["dob"]
        assert dumped["admission_date"] == row["admission_date"]


def test_roundtrip_intake_csv():
    csv_path = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "intake.csv"
    assert csv_path.exists(), f"intake.csv not found at {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 15, (
        f"Expected 15 intake rows (5 institutions * 3 programs), got {len(rows)}"
    )

    for row in rows:
        intake = ProgramIntake(**row)
        assert intake.approved_intake in [65, 75]
        assert isinstance(intake.supernumerary_allowed, dict)
        assert intake.supernumerary_allowed.get("TFW") == 5

        # Reconstructed
        json_str = intake.model_dump_json()
        reconstructed = ProgramIntake.model_validate_json(json_str)
        assert intake == reconstructed


def test_mock_registry_consistency():
    students_csv_path = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "students.csv"
    registry_csv_path = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "registry.csv"

    with open(students_csv_path, mode="r", encoding="utf-8") as f:
        students = list(csv.DictReader(f))

    with open(registry_csv_path, mode="r", encoding="utf-8") as f:
        registry = list(csv.DictReader(f))

    assert len(registry) == 1000
    reg_map = {r["apaar_id"]: r for r in registry}

    for s in students:
        apaar = s["apaar_id"]
        assert apaar in reg_map
        reg_row = reg_map[apaar]
        assert reg_row["full_name"] == s["full_name"]
        assert reg_row["dob"] == s["dob"]
        assert reg_row["gender"] == s["gender"]


def test_defects_json_structure():
    defects_path = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "defects.json"
    assert defects_path.exists()
    with open(defects_path, mode="r", encoding="utf-8") as f:
        defects = json.load(f)
    assert isinstance(defects, list)
    for defect in defects:
        assert "row" in defect
        assert "rule_id" in defect
        assert "field" in defect
        assert "description" in defect
