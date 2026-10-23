"""engine/tests/test_dedup_intra.py

Unit and integration tests for intra-batch duplicate detection (V009).
Owned by Team A (Data & Intelligence).
"""

import pandas as pd

from apaar_engine.dedup.intra import detect_intra_duplicates, score_pair
from apaar_engine.models import DuplicateScope, Severity


def test_score_pair_exact_and_variants():
    # Exact match
    assert score_pair("Aarav Verma", "Aarav Verma", "2005-04-02", "2005-04-02") == 1.0

    # Transliteration variant: Krishna vs Krushna
    s_krishna = score_pair("Krishna Joshi", "Krushna Joshi", "2005-04-02", "2005-04-02")
    assert s_krishna >= 0.92

    # Transliteration variant: Bhairoo vs Bheru
    s_bhairoo = score_pair("Bhairoo Sharma", "Bheru Sharma", "2005-04-02", "2005-04-02")
    assert s_bhairoo >= 0.92

    # Swapped name order: Aarav Verma vs Verma Aarav
    s_swapped = score_pair("Aarav Verma", "Verma Aarav", "2005-04-02", "2005-04-02")
    assert s_swapped == 1.0

    # Initials: A. K. Sharma vs Anil Kumar Sharma
    s_initials = score_pair("A. K. Sharma", "Anil Kumar Sharma", "2005-04-02", "2005-04-02")
    assert s_initials >= 0.92

    # Different DOB -> zero score
    assert score_pair("Krishna Joshi", "Krishna Joshi", "2005-04-02", "2005-04-03") == 0.0

    # Different forenames sharing surname -> non-duplicate (< 0.75)
    assert score_pair("Pranav Chatterjee", "Kabir Chatterjee", "2005-04-02", "2005-04-02") < 0.75


def test_detect_intra_duplicates_clusters_and_issues():
    data = [
        # Pair 1: Transliteration (>=0.92 -> FLAG)
        {
            "apaar_id": "111122223333",
            "full_name": "Krishna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
            "_row_num": 10,
        },
        {
            "apaar_id": "999988887777",
            "full_name": "Krushna Joshi",
            "dob": "2005-04-02",
            "gender": "M",
            "_row_num": 15,
        },
        # Pair 2: Swapped name order (>=0.92 -> FLAG)
        {
            "apaar_id": "222233334444",
            "full_name": "Aarav Verma",
            "dob": "2005-08-10",
            "gender": "M",
            "_row_num": 20,
        },
        {
            "apaar_id": "888877776666",
            "full_name": "Verma Aarav",
            "dob": "2005-08-10",
            "gender": "M",
            "_row_num": 25,
        },
        # Pair 3: Distinct students (different forenames, same DOB and surname) -> NO FLAG
        {
            "apaar_id": "333344445555",
            "full_name": "Pranav Chatterjee",
            "dob": "2006-03-19",
            "gender": "M",
            "_row_num": 30,
        },
        {
            "apaar_id": "777766665555",
            "full_name": "Kabir Chatterjee",
            "dob": "2006-03-19",
            "gender": "M",
            "_row_num": 35,
        },
    ]
    df = pd.DataFrame(data)
    issues, clusters = detect_intra_duplicates(df)

    flagged_rows = {iss.row for iss in issues if iss.rule_id == "V009"}
    assert flagged_rows == {10, 15, 20, 25}
    assert 30 not in flagged_rows
    assert 35 not in flagged_rows

    for iss in issues:
        assert iss.severity == Severity.WARN
        assert iss.field == "full_name"

    # Clusters generated
    assert len(clusters) == 2
    for cl in clusters:
        assert cl.scope == DuplicateScope.INTRA
        assert cl.score >= 0.92
        assert len(cl.apaar_ids) == 2
        assert cl.evidence["status"] == "FLAG"
