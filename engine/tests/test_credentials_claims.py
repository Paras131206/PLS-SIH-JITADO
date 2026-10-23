"""engine/tests/test_credentials_claims.py

Unit tests for SD-JWT credential claim builder (Phase 4, Team A).
Verifies that student records are converted into verifiable claims with
selective disclosure markings and issuer metadata.
"""

import json

from apaar_engine.credentials.claims import (
    ISSUER_METADATA_KEYS,
    SELECTIVELY_DISCLOSABLE_KEYS,
    _b64url_decode,
    create_disclosure,
    create_presentation,
    from_student_record,
)
from apaar_engine.models import StudentRecord


def test_from_student_record_claims_and_metadata():
    student_data = {
        "apaar_id": "111122223333",
        "institution_aicte_id": "1-10001",
        "institution_student_id": "CSE-2026-042",
        "full_name": "Aarav Sharma",
        "dob": "2005-08-15",
        "gender": "M",
        "category": "GEN",
        "pwd": "False",
        "program_code": "UG-CSE",
        "course_level": "UG",
        "academic_year": "2026-27",
        "admission_date": "2026-07-15",
        "admission_type": "REGULAR",
        "seat_type": "REGULAR",
        "supernumerary_scheme": "",
        "quota": "NONE",
        "nationality": "IN",
        "nri_status": "False",
        "oci_status": "False",
        "fn_status": "False",
        "enrolment_status": "ACTIVE",
        "consent_status": "GRANTED",
        "consent_date": "2026-07-10",
        "guardian_consent": "",
        "email": "aarav.sharma@example.edu.in",
        "mobile": "9876543210",
    }
    student_obj = StudentRecord.model_validate(student_data)

    claim_bundle = from_student_record(
        student_obj,
        issuer="did:web:aicte.gov.in:institutions:1-10001",
        issued_at=1774320000,
    )

    # 1. Verify Issuer Metadata (Non-disclosable)
    issuer_meta = claim_bundle["issuer_metadata"]
    assert issuer_meta["iss"] == "did:web:aicte.gov.in:institutions:1-10001"
    assert issuer_meta["iat"] == 1774320000
    assert issuer_meta["vct"] == "urn:aicte:credentials:admission:v1"
    assert "jti" in issuer_meta
    for k in issuer_meta:
        assert k in ISSUER_METADATA_KEYS
        # Must NOT be marked as selectively disclosable
        assert claim_bundle["_sd_marked"][k] is False

    # 2. Verify Selectively Disclosable Claims
    claims = claim_bundle["claims"]
    assert claims["apaar_id"] == "111122223333"
    assert claims["institution_student_id"] == "CSE-2026-042"
    assert claims["full_name"] == "Aarav Sharma"
    assert claims["program"] == "UG-CSE"
    assert claims["course_level"] == "UG"
    assert claims["academic_year"] == "2026-27"
    assert claims["enrolment_status"] == "ACTIVE"

    # Quota flags verification
    q_flags = claims["quota_flags"]
    assert q_flags["quota"] == "NONE"
    assert q_flags["is_nri"] is False
    assert q_flags["is_oci"] is False
    assert q_flags["is_fn"] is False
    assert q_flags["seat_type"] == "REGULAR"

    # All disclosable keys must be marked True in _sd_marked
    for key in SELECTIVELY_DISCLOSABLE_KEYS:
        assert claim_bundle["_sd_marked"][key] is True
        assert key in claim_bundle["selective_disclosures"]

    # 3. Verify RFC SD-JWT Digests and Disclosures
    sd_digests = claim_bundle["_sd"]
    assert len(sd_digests) == len(SELECTIVELY_DISCLOSABLE_KEYS)
    assert len(claim_bundle["_disclosures"]) == len(SELECTIVELY_DISCLOSABLE_KEYS)

    # Validate that every disclosure decodes to [salt, claim_name, claim_value]
    for claim_name, disc_b64 in claim_bundle["_disclosures"].items():
        raw_json = _b64url_decode(disc_b64).decode("utf-8")
        parsed = json.loads(raw_json)
        assert len(parsed) == 3
        salt, name, val = parsed
        assert name == claim_name
        assert val == claims[claim_name]


def test_create_presentation_selective_disclosure():
    student_dict = {
        "apaar_id": "999988887777",
        "institution_aicte_id": "1-10002",
        "institution_student_id": "MECH-2026-005",
        "full_name": "Rohan Deshmukh",
        "program_code": "UG-MECH",
        "course_level": "UG",
        "academic_year": "2026-27",
        "enrolment_status": "ACTIVE",
        "quota": "NRI",
        "nri_status": True,
        "seat_type": "REGULAR",
    }

    claim_bundle = from_student_record(student_dict)

    # Student presents credential to employer: only discloses full_name, program, course_level
    # Hidden claims: apaar_id, institution_student_id, quota_flags, academic_year, enrolment_status
    presentation = create_presentation(
        claim_bundle,
        disclosed_keys=["full_name", "program", "course_level"],
    )

    p_claims = presentation["presentation_claims"]

    # Disclosed claims must be present
    assert p_claims["full_name"] == "Rohan Deshmukh"
    assert p_claims["program"] == "UG-MECH"
    assert p_claims["course_level"] == "UG"

    # Issuer metadata must be retained
    assert "iss" in p_claims
    assert "iat" in p_claims
    assert "vct" in p_claims

    # Undisclosed claims must NOT be in presentation_claims
    assert "apaar_id" not in p_claims
    assert "institution_student_id" not in p_claims
    assert "quota_flags" not in p_claims

    # Disclosures array must only contain the 3 disclosed claims
    assert len(presentation["disclosures"]) == 3
    assert presentation["disclosed_keys"] == ["course_level", "full_name", "program"]


def test_create_disclosure_reproducibility():
    disc_1, digest_1 = create_disclosure("full_name", "Aarav Sharma", salt="fixed_salt_12345")
    disc_2, digest_2 = create_disclosure("full_name", "Aarav Sharma", salt="fixed_salt_12345")

    assert disc_1 == disc_2
    assert digest_1 == digest_2

    # Different salt must yield different disclosure and digest
    disc_3, digest_3 = create_disclosure("full_name", "Aarav Sharma", salt="other_salt_99999")
    assert disc_1 != disc_3
    assert digest_1 != digest_3
