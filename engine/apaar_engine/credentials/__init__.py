"""engine/apaar_engine/credentials/__init__.py

Credentials module for APAAR-SDMS:
- SD-JWT claim builder from student record
- Selective disclosure formatting and presentations
"""

from apaar_engine.credentials.claims import (
    ISSUER_METADATA_KEYS,
    SELECTIVELY_DISCLOSABLE_KEYS,
    create_disclosure,
    create_presentation,
    from_student_record,
)

__all__ = [
    "ISSUER_METADATA_KEYS",
    "SELECTIVELY_DISCLOSABLE_KEYS",
    "create_disclosure",
    "create_presentation",
    "from_student_record",
]
