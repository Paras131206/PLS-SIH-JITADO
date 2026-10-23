"""engine/apaar_engine/credentials/claims.py

SD-JWT (Selective Disclosure JWT) credential claim builder for APAAR-SDMS.
Builds verifiable credential claims from student records, designating
student identity, program, and quota flags as selectively disclosable,
while retaining issuer metadata as non-disclosable top-level claims.

Conforms to IETF SD-JWT specification concepts (RFC-compliant disclosure hashing).
Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

import pandas as pd

from apaar_engine.models import StudentRecord

# Standard claims marked as selectively disclosable per agents.md / Phase 4 specification
SELECTIVELY_DISCLOSABLE_KEYS: Set[str] = {
    "apaar_id",
    "institution_student_id",
    "full_name",
    "program",
    "course_level",
    "academic_year",
    "enrolment_status",
    "quota_flags",
}

# Top-level non-disclosable issuer metadata claims
ISSUER_METADATA_KEYS: Set[str] = {
    "iss",
    "iat",
    "exp",
    "nbf",
    "vct",
    "jti",
    "status",
}


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode with automatic padding."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_disclosure(
    key: str,
    value: Any,
    salt: Optional[str] = None,
) -> Tuple[str, str]:
    """Create an SD-JWT disclosure and its SHA-256 digest.

    Disclosure format: base64url(json([salt, claim_name, claim_value]))
    Digest: base64url(sha256(disclosure_string))
    """
    if salt is None:
        salt = secrets.token_urlsafe(16)

    disclosure_payload = [salt, key, value]
    raw_json = json.dumps(disclosure_payload, separators=(",", ":"), ensure_ascii=False)
    disclosure_b64 = _b64url_encode(raw_json.encode("utf-8"))

    digest_bytes = hashlib.sha256(disclosure_b64.encode("ascii")).digest()
    digest_b64 = _b64url_encode(digest_bytes)

    return disclosure_b64, digest_b64


def from_student_record(
    record: Union[StudentRecord, Dict[str, Any], pd.Series],
    issuer: Optional[str] = None,
    issued_at: Optional[int] = None,
    expiry_seconds: Optional[int] = None,
    credential_id: Optional[str] = None,
    vct: str = "urn:aicte:credentials:admission:v1",
) -> Dict[str, Any]:
    """Build SD-JWT claims dictionary from a StudentRecord or student dict.

    - Selectively disclosable:
      apaar_id, institution_student_id, full_name, program, course_level,
      academic_year, enrolment_status, quota_flags (quota, is_nri, is_oci, is_fn,
      seat_type, supernumerary_scheme).
    - Non-disclosable issuer metadata:
      iss, iat, exp, vct, jti.

    Returns a rich SD-JWT claim structure containing:
      - 'issuer_metadata': non-disclosable headers & claims (iss, iat, vct, jti)
      - 'claims': clean dictionary of all claims
      - 'selective_disclosures': map of disclosable claim name -> value
      - '_sd_marked': boolean mapping of key -> is_selectively_disclosable
      - '_sd': array of SHA-256 disclosure digests (IETF SD-JWT payload)
      - '_disclosures': map of claim name -> base64url disclosure string
    """
    if isinstance(record, StudentRecord):
        rec = record.model_dump(mode="json")
    elif isinstance(record, pd.Series):
        rec = record.to_dict()
    elif isinstance(record, dict):
        rec = dict(record)
    else:
        raise TypeError(f"Unsupported record type: {type(record)}")

    def _val(v: Any) -> str:
        if v is None:
            return ""
        if hasattr(v, "value"):
            return str(v.value).strip()
        return str(v).strip()

    now_ts = int(time.time()) if issued_at is None else int(issued_at)
    jti = credential_id or f"urn:uuid:{uuid4()}"
    inst_id = _val(rec.get("institution_aicte_id") or "AICTE")
    iss = issuer or f"did:web:aicte.gov.in:institutions:{inst_id}"

    # Extract disclosable claims
    apaar_id = _val(rec.get("apaar_id"))
    institution_student_id = _val(rec.get("institution_student_id"))
    full_name = _val(rec.get("full_name"))
    program = _val(rec.get("program_code") or rec.get("program"))
    course_level = _val(rec.get("course_level"))
    academic_year = _val(rec.get("academic_year"))
    enrolment_status = _val(rec.get("enrolment_status") or "ACTIVE").upper()

    def _to_bool(val: Any) -> bool:
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("true", "1", "yes", "t")

    quota_flags = {
        "quota": _val(rec.get("quota") or "NONE").upper(),
        "is_nri": _to_bool(rec.get("nri_status", False)),
        "is_oci": _to_bool(rec.get("oci_status", False)),
        "is_fn": _to_bool(rec.get("fn_status", False)),
        "seat_type": _val(rec.get("seat_type") or "REGULAR").upper(),
        "supernumerary_scheme": _val(rec.get("supernumerary_scheme") or "").upper(),
    }

    disclosable_claims: Dict[str, Any] = {
        "apaar_id": apaar_id,
        "institution_student_id": institution_student_id,
        "full_name": full_name,
        "program": program,
        "course_level": course_level,
        "academic_year": academic_year,
        "enrolment_status": enrolment_status,
        "quota_flags": quota_flags,
    }

    # Generate IETF SD-JWT disclosures and digests
    sd_digests: List[str] = []
    disclosures_map: Dict[str, str] = {}
    for claim_name, claim_val in disclosable_claims.items():
        disc_b64, digest_b64 = create_disclosure(claim_name, claim_val)
        sd_digests.append(digest_b64)
        disclosures_map[claim_name] = disc_b64

    # Sort digests deterministically
    sd_digests.sort()

    issuer_metadata: Dict[str, Any] = {
        "iss": iss,
        "iat": now_ts,
        "vct": vct,
        "jti": jti,
    }
    if expiry_seconds:
        issuer_metadata["exp"] = now_ts + expiry_seconds

    # Combine all claims with selective disclosure markings
    claims_dict: Dict[str, Any] = {**issuer_metadata, **disclosable_claims}
    sd_marked_map: Dict[str, bool] = {k: (k in SELECTIVELY_DISCLOSABLE_KEYS) for k in claims_dict}

    return {
        "issuer_metadata": issuer_metadata,
        "claims": claims_dict,
        "selective_disclosures": disclosable_claims,
        "_sd_marked": sd_marked_map,
        "_sd": sd_digests,
        "_disclosures": disclosures_map,
    }


def create_presentation(
    claim_bundle: Dict[str, Any],
    disclosed_keys: List[str],
) -> Dict[str, Any]:
    """Create a selective disclosure presentation revealing only requested claims.

    Undisclosed claims remain hidden behind their SHA-256 digests in _sd,
    while disclosed claims include their cleartext values and disclosure tokens.
    """
    disclosed_set = set(disclosed_keys)
    issuer_metadata = dict(claim_bundle["issuer_metadata"])
    all_disclosures = claim_bundle["_disclosures"]
    all_claims = claim_bundle["selective_disclosures"]

    revealed_claims: Dict[str, Any] = dict(issuer_metadata)
    included_disclosures: List[str] = []

    for k in disclosed_set:
        if k in all_claims:
            revealed_claims[k] = all_claims[k]
        if k in all_disclosures:
            included_disclosures.append(all_disclosures[k])

    return {
        "presentation_claims": revealed_claims,
        "disclosed_keys": sorted(disclosed_set),
        "disclosures": included_disclosures,
        "issuer": issuer_metadata.get("iss"),
        "issued_at": issuer_metadata.get("iat"),
        "credential_id": issuer_metadata.get("jti"),
    }
