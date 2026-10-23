"""engine/tests/test_rules_phase2.py

Unit tests for Phase 2 validation rules:
- V003: apaar_id not in APAAR registry
- V004: APAAR registry name/dob mismatch (fuzzy)
- V012: Regular enrolment > approved intake
- V013: Supernumerary count > allowed per scheme
- V014: Quota/nationality inconsistent (OCI/FN with IN, NRI flag mismatch)
- V015: seat_type=SUPERNUMERARY with no scheme, or scheme on regular seat
- V016: Age implausible for course_level
- V017: admission_date outside academic window
- V018: consent missing or under 18 without guardian_consent
- V019: program_code not in approved programs

Owned by Team A (Data & Intelligence).
"""

import pandas as pd

from apaar_engine.registry import MockApaarRegistry
from apaar_engine.rules.registry import run_rule


def test_v003_and_v004_registry():
    registry = MockApaarRegistry(
        {
            "123456789012": {"name": "Aarav Sharma", "dob": "2005-05-10"},
            "987654321098": {"name": "Priya Patel", "dob": "2006-06-20"},
        }
    )

    data = [
        {
            "apaar_id": "123456789012",
            "full_name": "Aarav Sharma",
            "dob": "2005-05-10",
            "_row_num": 2,
        },
        {
            "apaar_id": "111122223333",
            "full_name": "Unknown",
            "dob": "2005-05-10",
            "_row_num": 3,
        },  # V003
        {
            "apaar_id": "987654321098",
            "full_name": "Priya Patel",
            "dob": "2007-01-01",
            "_row_num": 4,
        },  # V004 dob mismatch
        {
            "apaar_id": "987654321098",
            "full_name": "Completely Different",
            "dob": "2006-06-20",
            "_row_num": 5,
        },  # V004 name mismatch
    ]
    df = pd.DataFrame(data)

    issues_v003 = run_rule("V003", df, registry=registry)
    assert len(issues_v003) == 1
    assert issues_v003[0].row == 3
    assert issues_v003[0].rule_id == "V003"

    issues_v004 = run_rule("V004", df, registry=registry)
    assert len(issues_v004) == 2
    assert {iss.row for iss in issues_v004} == {4, 5}


def test_v012_regular_intake_exceeded():
    intake_df = pd.DataFrame(
        [{"institution_aicte_id": "1-10001", "program_code": "UG-CSE", "approved_intake": 2}]
    )
    data = [
        {"program_code": "UG-CSE", "seat_type": "REGULAR", "_row_num": 2},
        {"program_code": "UG-CSE", "seat_type": "REGULAR", "_row_num": 3},
        {"program_code": "UG-CSE", "seat_type": "REGULAR", "_row_num": 4},  # Exceeds intake 2
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V012", df, intake_df=intake_df)
    assert len(issues) == 1
    assert issues[0].row == 4
    assert issues[0].rule_id == "V012"


def test_v013_supernumerary_limits():
    intake_df = pd.DataFrame(
        [
            {
                "institution_aicte_id": "1-10001",
                "program_code": "UG-CSE",
                "approved_intake": 60,
                "supernumerary_allowed": '{"TFW": 1}',
            }
        ]
    )
    data = [
        {
            "program_code": "UG-CSE",
            "seat_type": "SUPERNUMERARY",
            "supernumerary_scheme": "TFW",
            "_row_num": 2,
        },
        {
            "program_code": "UG-CSE",
            "seat_type": "SUPERNUMERARY",
            "supernumerary_scheme": "TFW",
            "_row_num": 3,
        },  # Exceeds TFW limit 1
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V013", df, intake_df=intake_df)
    assert len(issues) == 1
    assert issues[0].row == 3
    assert issues[0].rule_id == "V013"


def test_v014_quota_nationality_consistency():
    data = [
        {
            "quota": "OCI",
            "nationality": "IN",
            "nri_status": "False",
            "oci_status": "True",
            "fn_status": "False",
            "_row_num": 2,
        },  # OCI with IN
        {
            "quota": "FN",
            "nationality": "IN",
            "nri_status": "False",
            "oci_status": "False",
            "fn_status": "True",
            "_row_num": 3,
        },  # FN with IN
        {
            "quota": "NRI",
            "nationality": "IN",
            "nri_status": "False",
            "oci_status": "False",
            "fn_status": "False",
            "_row_num": 4,
        },  # NRI quota but nri_status False
        {
            "quota": "NONE",
            "nationality": "IN",
            "nri_status": "True",
            "oci_status": "False",
            "fn_status": "False",
            "_row_num": 5,
        },  # nri_status True but quota NONE
        {
            "quota": "NONE",
            "nationality": "IN",
            "nri_status": "False",
            "oci_status": "False",
            "fn_status": "False",
            "_row_num": 6,
        },  # Valid
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V014", df)
    assert len(issues) == 4
    assert {iss.row for iss in issues} == {2, 3, 4, 5}


def test_v015_seat_and_scheme_consistency():
    data = [
        {
            "seat_type": "SUPERNUMERARY",
            "supernumerary_scheme": "",
            "_row_num": 2,
        },  # Supernumerary with no scheme
        {
            "seat_type": "REGULAR",
            "supernumerary_scheme": "TFW",
            "_row_num": 3,
        },  # Scheme on regular seat
        {"seat_type": "REGULAR", "supernumerary_scheme": "", "_row_num": 4},  # Valid
        {"seat_type": "SUPERNUMERARY", "supernumerary_scheme": "TFW", "_row_num": 5},  # Valid
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V015", df)
    assert len(issues) == 2
    assert {iss.row for iss in issues} == {2, 3}


def test_v016_age_vs_course_level():
    data = [
        {
            "dob": "2018-01-01",
            "course_level": "UG",
            "admission_date": "2026-07-15",
            "_row_num": 2,
        },  # Age 8: implausible
        {
            "dob": "2005-01-01",
            "course_level": "UG",
            "admission_date": "2026-07-15",
            "_row_num": 3,
        },  # Age 21: valid
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V016", df)
    assert len(issues) == 1
    assert issues[0].row == 2
    assert issues[0].rule_id == "V016"


def test_v017_admission_window():
    data = [
        {
            "admission_date": "2025-01-01",
            "academic_year": "2026-27",
            "_row_num": 2,
        },  # Outside window
        {
            "admission_date": "2026-07-15",
            "academic_year": "2026-27",
            "_row_num": 3,
        },  # Inside window
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V017", df)
    assert len(issues) == 1
    assert issues[0].row == 2
    assert issues[0].rule_id == "V017"


def test_v018_consent_and_minor_guardian():
    data = [
        {
            "consent_status": "REFUSED",
            "dob": "2005-01-01",
            "admission_date": "2026-07-15",
            "guardian_consent": "False",
            "_row_num": 2,
        },  # Refused consent
        {
            "consent_status": "GRANTED",
            "dob": "2009-08-01",
            "admission_date": "2026-07-15",
            "guardian_consent": "False",
            "_row_num": 3,
        },  # Minor without guardian consent
        {
            "consent_status": "GRANTED",
            "dob": "2009-08-01",
            "admission_date": "2026-07-15",
            "guardian_consent": "True",
            "_row_num": 4,
        },  # Valid minor with guardian consent
        {
            "consent_status": "GRANTED",
            "dob": "2005-01-01",
            "admission_date": "2026-07-15",
            "guardian_consent": "False",
            "_row_num": 5,
        },  # Valid adult
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V018", df)
    assert len(issues) == 2
    assert {iss.row for iss in issues} == {2, 3}


def test_v019_unapproved_program():
    intake_df = pd.DataFrame([{"institution_aicte_id": "1-10001", "program_code": "UG-CSE"}])
    data = [
        {"program_code": "UG-CSE", "_row_num": 2},  # Approved
        {"program_code": "UG-AEROSPACE", "_row_num": 3},  # Unapproved
    ]
    df = pd.DataFrame(data)
    issues = run_rule("V019", df, intake_df=intake_df)
    assert len(issues) == 1
    assert issues[0].row == 3
    assert issues[0].rule_id == "V019"
