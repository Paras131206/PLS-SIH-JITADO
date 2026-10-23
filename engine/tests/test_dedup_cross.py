"""engine/tests/test_dedup_cross.py

Unit and integration tests for cross-institution duplicate detection (V010, V011).
Owned by Team A (Data & Intelligence).
"""

import pandas as pd

from apaar_engine.dedup.cross import detect_cross_duplicates
from apaar_engine.models import DuplicateScope, Severity


def test_v010_cross_institution_active_apaar():
    batch_data = [
        {
            "apaar_id": "111122223333",
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Krishna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
            "_row_num": 10,
        },
        {
            "apaar_id": "444455556666",
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Aarav Verma",
            "dob": "2005-08-10",
            "gender": "M",
            "_row_num": 12,
        },
    ]
    central_data = [
        # Exactly same APAAR ACTIVE at another institution (1-10002) in same year -> triggers V010
        {
            "apaar_id": "111122223333",
            "institution_aicte_id": "1-10002",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Krishna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
        },
        # Different APAAR and different student -> no flag
        {
            "apaar_id": "888899990000",
            "institution_aicte_id": "1-10003",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Pari Agarwal",
            "dob": "2006-05-15",
            "gender": "F",
        },
    ]

    batch_df = pd.DataFrame(batch_data)
    central_df = pd.DataFrame(central_data)

    issues, clusters = detect_cross_duplicates(batch_df, central_df)

    v010_issues = [iss for iss in issues if iss.rule_id == "V010"]
    assert len(v010_issues) == 1
    assert v010_issues[0].row == 10
    assert v010_issues[0].severity == Severity.ERROR
    assert "1-10002" in v010_issues[0].message

    v010_clusters = [c for c in clusters if c.evidence and c.evidence.get("rule_id") == "V010"]
    assert len(v010_clusters) == 1
    assert v010_clusters[0].scope == DuplicateScope.CROSS_INSTITUTION
    assert v010_clusters[0].score == 1.0
    assert v010_clusters[0].evidence["central_institution"] == "1-10002"


def test_v011_splink_cross_institution_fuzzy_match():
    batch_data = [
        {
            "apaar_id": "111122223333",
            "institution_aicte_id": "1-10001",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Krishna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
            "_row_num": 15,
        }
    ]
    central_data = [
        # Probable same person under DIFFERENT APAAR at another institution
        # (1-10003) -> triggers V011
        {
            "apaar_id": "999988887777",
            "institution_aicte_id": "1-10003",
            "academic_year": "2026-27",
            "enrolment_status": "ACTIVE",
            "full_name": "Krushna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
        }
    ]

    batch_df = pd.DataFrame(batch_data)
    central_df = pd.DataFrame(central_data)

    issues, clusters = detect_cross_duplicates(batch_df, central_df)

    v011_issues = [iss for iss in issues if iss.rule_id == "V011"]
    assert len(v011_issues) == 1
    assert v011_issues[0].row == 15
    assert v011_issues[0].severity == Severity.WARN

    v011_clusters = [c for c in clusters if c.evidence and c.evidence.get("rule_id") == "V011"]
    assert len(v011_clusters) == 1
    assert v011_clusters[0].scope == DuplicateScope.CROSS_INSTITUTION
    assert v011_clusters[0].score >= 0.75
    assert v011_clusters[0].evidence["central_institution"] == "1-10003"
