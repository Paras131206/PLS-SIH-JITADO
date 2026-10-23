"""engine/tests/test_normalize_soundex.py

Unit tests for Indian name normalization and Indic-soundex phonetic encoding.
Owned by Team A (Data & Intelligence).
"""

from apaar_engine.dedup.normalize import (
    canonicalize_token,
    get_name_tokens,
    indic_soundex,
    normalize_indian_name,
    sorted_name_tokens,
)


def test_strip_honorifics():
    names = [
        ("Shri Krishna Sharma", "KRISHNA SHARMA"),
        ("Smt. Sunita Verma", "SUNITA VERMA"),
        ("Kumari Kavya Bhat", "KAVYA BHAT"),
        ("Dr. Rajesh Gupta", "RAJESH GUPTA"),
        ("Mr. Vivaan Joshi", "VIVAAN JOSHI"),
        ("Mrs. Ananya Rao", "ANANYA RAO"),
        ("Ms. Swati Iyer", "SWATI IYER"),
        ("Mohd. Reyansh Khan", "REYANSH KHAN"),
        ("Er. Pranav Reddy", "PRANAV REDDY"),
        ("Prof. Dr. Atharva Kumar", "ATHARVA KUMAR"),
    ]
    for raw, expected in names:
        assert normalize_indian_name(raw) == expected, f"Failed for {raw}"


def test_punctuation_and_initials():
    assert normalize_indian_name("A. K. Sharma") == "A K SHARMA"
    assert normalize_indian_name("R.-K. Gupta") == "R K GUPTA"
    assert normalize_indian_name("  S.   Priyadarshini  ") == "S PRIYADARSHINI"
    assert get_name_tokens("A. K. Sharma") == ["A", "K", "SHARMA"]


def test_sorted_name_tokens_order_invariance():
    assert sorted_name_tokens("Sharma Krishna") == "KRISHNA SHARMA"
    assert sorted_name_tokens("Krishna Sharma") == "KRISHNA SHARMA"
    assert sorted_name_tokens("Verma Aarav Kumar") == "AARAV KUMAR VERMA"
    assert sorted_name_tokens("Kumar Aarav Verma") == "AARAV KUMAR VERMA"


def test_canonicalize_transliteration():
    assert canonicalize_token("BHAIROO") == "BHERU"
    assert canonicalize_token("BHERU") == "BHERU"
    assert canonicalize_token("KRUSHNA") == "KRISHNA"
    assert canonicalize_token("CHOUDHARY") == "CHOWDHURY"
    assert canonicalize_token("LAKSHMI") == "LAXMI"


def test_indic_soundex_equivalences():
    # Krishna vs Krushna
    assert indic_soundex("Krishna") == indic_soundex("Krushna")
    assert indic_soundex("Krishna") == "K625"

    # Bhairoo vs Bheru
    assert indic_soundex("Bhairoo") == indic_soundex("Bheru")
    assert indic_soundex("Bhairoo") == "B600"

    # Digraphs and Aspirates
    assert indic_soundex("Sharma") == "S650"
    assert indic_soundex("Verma") == "V650"
    assert indic_soundex("Joshi") == "J200"

    # Empty token safe
    assert indic_soundex("") == "0000"
