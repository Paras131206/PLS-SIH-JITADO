"""engine/tests/test_models.py

Unit tests for Pydantic v2 models and rule catalog consistency.
Owned by Team A (Data & Intelligence).
"""

from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from apaar_engine.models import (
    AdmissionType,
    Anomaly,
    BatchReport,
    Category,
    ConsentStatus,
    CourseLevel,
    DuplicateCluster,
    DuplicateScope,
    EnrolmentStatus,
    Gender,
    IntakeSummary,
    Issue,
    ProgramIntake,
    Quota,
    SeatType,
    Severity,
    StudentRecord,
    mask_apaar,
)


def test_mask_apaar():
    assert mask_apaar("123456789012") == "1234****9012"
    assert mask_apaar("987654321098") == "9876****1098"
    assert mask_apaar("") == ""
    assert mask_apaar(None) == ""
    assert mask_apaar("123") == "****"


def test_student_record_valid():
    record = StudentRecord(
        apaar_id="123456789012",
        institution_aicte_id="1-10001",
        institution_student_id="2026-CSE-001",
        full_name="Aarav Sharma",
        dob=date(2005, 5, 10),
        gender=Gender.M,
        category=Category.GEN,
        pwd=False,
        program_code="UG-CSE",
        course_level=CourseLevel.UG,
        academic_year="2026-27",
        admission_date=date(2026, 7, 15),
        admission_type=AdmissionType.REGULAR,
        seat_type=SeatType.REGULAR,
        supernumerary_scheme=None,
        quota=Quota.NONE,
        nationality="IN",
        nri_status=False,
        oci_status=False,
        fn_status=False,
        enrolment_status=EnrolmentStatus.ACTIVE,
        consent_status=ConsentStatus.GRANTED,
        consent_date=date(2026, 7, 10),
        guardian_consent=None,
        email="aarav.sharma@example.edu.in",
        mobile="9876543210",
    )
    assert record.apaar_id == "123456789012"
    assert record.apaar_masked == "1234****9012"
    assert record.pwd is False


def test_student_record_invalid_enum():
    with pytest.raises(ValidationError):
        StudentRecord(
            apaar_id="123456789012",
            institution_aicte_id="1-10001",
            institution_student_id="2026-CSE-001",
            full_name="Aarav Sharma",
            dob=date(2005, 5, 10),
            gender="INVALID_GENDER",  # Invalid
            category=Category.GEN,
            program_code="UG-CSE",
            course_level=CourseLevel.UG,
            academic_year="2026-27",
            admission_date=date(2026, 7, 15),
            admission_type=AdmissionType.REGULAR,
            seat_type=SeatType.REGULAR,
            quota=Quota.NONE,
            nationality="IN",
            nri_status=False,
            oci_status=False,
            fn_status=False,
            enrolment_status=EnrolmentStatus.ACTIVE,
            consent_status=ConsentStatus.GRANTED,
        )


def test_program_intake_model():
    intake = ProgramIntake(
        institution_aicte_id="1-10001",
        program_code="UG-CSE",
        academic_year="2026-27",
        approved_intake=75,
        supernumerary_allowed={"TFW": 5, "PMSSS": 5},
        approval_letter_ref="AICTE/EOA/2026-27/1-10001/UG-CSE",
    )
    assert intake.approved_intake == 75
    assert intake.supernumerary_allowed["TFW"] == 5

    # Test string parsing of supernumerary_allowed
    intake_from_str = ProgramIntake(
        institution_aicte_id="1-10001",
        program_code="UG-CSE",
        academic_year="2026-27",
        approved_intake=75,
        supernumerary_allowed='{"TFW": 5, "PMSSS": 5}',
        approval_letter_ref="AICTE/EOA/2026-27/1-10001/UG-CSE",
    )
    assert intake_from_str.supernumerary_allowed == {"TFW": 5, "PMSSS": 5}


def test_batch_report_structure():
    report = BatchReport(
        batch_id="b7f1418b-5975-4d76-8fe9-2b0244439162",
        institution_aicte_id="1-10001",
        rows_total=100,
        rows_valid=98,
        rows_warning=1,
        rows_error=1,
        quality_score=98.5,
        metrics={"completeness": {"dob": 1.0}, "uniqueness": {"apaar_id": 0.99}},
        issues=[
            Issue(
                row=12,
                field="apaar_id",
                rule_id="V002",
                severity=Severity.ERROR,
                message="apaar_id missing or not 12 digits",
                value_masked="1234****9012",
            )
        ],
        intake_summary=[
            IntakeSummary(
                program_code="UG-CSE",
                approved=75,
                enrolled=70,
                supernumerary=3,
                excess=0,
            )
        ],
        duplicate_clusters=[
            DuplicateCluster(
                cluster_id="clust-001",
                apaar_ids=["123456789012", "987654321098"],
                score=0.95,
                scope=DuplicateScope.INTRA,
            )
        ],
        anomalies=[
            Anomaly(
                metric="nri_share",
                value=0.4,
                baseline=0.05,
                z=6.1,
                reason="NRI share 40% exceeds baseline 5%",
            )
        ],
    )
    data = report.model_dump()
    assert data["rows_total"] == 100
    assert len(data["issues"]) == 1
    assert data["issues"][0]["rule_id"] == "V002"
    assert len(data["duplicate_clusters"]) == 1


def test_rule_catalog_yaml_exact_v001_v020():
    catalog_path = Path(__file__).resolve().parents[2] / "contracts" / "rule_catalog.yaml"
    assert catalog_path.exists(), f"Rule catalog not found at {catalog_path}"

    with open(catalog_path, encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    rules = catalog.get("rules", [])
    assert len(rules) == 20, f"Expected 20 rules, found {len(rules)}"

    expected_ids = [f"V{i:03d}" for i in range(1, 21)]
    found_ids = [r["id"] for r in rules]
    assert found_ids == expected_ids

    for rule in rules:
        assert "id" in rule
        assert rule["severity"] in ["ERROR", "WARN"]
        assert "description" in rule and len(rule["description"]) > 0
        assert "fields" in rule and isinstance(rule["fields"], list)
        assert "params" in rule and isinstance(rule["params"], dict)
