"""engine/tests/test_rules_phase1.py

Unit tests for Phase 1 vectorized validation rules:
V001, V002, V005, V006, V007, V008.

Owned by Team A (Data & Intelligence).
"""

import pandas as pd

from apaar_engine.rules.registry import load_rule_catalog, run_rule


def test_v001_missing_header():
    # Missing 'gender', 'dob', 'full_name'
    df = pd.DataFrame([{"apaar_id": "123456789012", "program_code": "UG-CSE"}])
    issues = run_rule("V001", df)
    missing_fields = {iss.field for iss in issues}
    assert "gender" in missing_fields
    assert "dob" in missing_fields
    assert "full_name" in missing_fields
    assert all(iss.rule_id == "V001" for iss in issues)


def test_v002_apaar_format():
    data = [
        {"apaar_id": "123456789012", "_row_num": 2},  # Valid
        {"apaar_id": "12345678901", "_row_num": 3},  # 11 digits
        {"apaar_id": "1234567890123", "_row_num": 4},  # 13 digits
        {"apaar_id": "12345678901A", "_row_num": 5},  # Non-digit
        {"apaar_id": "", "_row_num": 6},  # Empty
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V002", df)
    assert len(issues) == 4
    issue_rows = {iss.row for iss in issues}
    assert issue_rows == {3, 4, 5, 6}


def test_v005_required_fields():
    data = [
        {"full_name": "Aarav Sharma", "dob": "2005-05-10", "_row_num": 2},
        {"full_name": "", "dob": "2005-05-10", "_row_num": 3},
        {"full_name": "Priya", "dob": "", "_row_num": 4},
        {"full_name": "None", "dob": "2005-05-10", "_row_num": 5},
    ]
    df = pd.DataFrame(data)
    catalog = load_rule_catalog()
    issues = run_rule("V005", df, catalog=catalog)
    # Row 3 full_name empty, Row 4 dob empty, Row 5 full_name="None"
    flagged = [(iss.row, iss.field) for iss in issues]
    assert (3, "full_name") in flagged
    assert (4, "dob") in flagged
    assert (5, "full_name") in flagged


def test_v006_format_checks():
    data = [
        {
            "dob": "2005/05/10",  # Bad date
            "admission_date": "2026-07-01",
            "gender": "X",  # Bad enum
            "category": "GENERAL",  # Bad enum
            "nationality": "INDIA",  # Bad ISO
            "email": "not_an_email",  # Bad email
            "mobile": "12345",  # Bad mobile
            "_row_num": 2,
        },
        {
            "dob": "2005-05-10",  # Good
            "admission_date": "2026-07-01",
            "gender": "M",
            "category": "GEN",
            "nationality": "IN",
            "email": "valid@example.com",
            "mobile": "9876543210",
            "_row_num": 3,
        },
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V006", df)
    bad_fields = {iss.field for iss in issues if iss.row == 2}
    assert "dob" in bad_fields
    assert "gender" in bad_fields
    assert "category" in bad_fields
    assert "nationality" in bad_fields
    assert "email" in bad_fields
    assert "mobile" in bad_fields
    # No issues for row 3
    assert not any(iss.row == 3 for iss in issues)


def test_v007_duplicate_apaar():
    data = [
        {"apaar_id": "111122223333", "_row_num": 2},
        {"apaar_id": "999988887777", "_row_num": 3},
        {"apaar_id": "111122223333", "_row_num": 4},  # Duplicate of row 2
        {"apaar_id": "444455556666", "_row_num": 5},
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V007", df)
    assert len(issues) == 2
    assert {iss.row for iss in issues} == {2, 4}


def test_v008_duplicate_student_id():
    data = [
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "institution_student_id": "CSE-01",
            "_row_num": 2,
        },
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "institution_student_id": "CSE-02",
            "_row_num": 3,
        },
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "institution_student_id": "CSE-01",
            "_row_num": 4,  # Duplicate within same inst & year
        },
        {
            "institution_aicte_id": "1-10002",
            "academic_year": "2026-27",
            "institution_student_id": "CSE-01",
            "_row_num": 5,  # Different institution: allowed
        },
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V008", df)
    assert len(issues) == 2
    assert {iss.row for iss in issues} == {2, 4}
