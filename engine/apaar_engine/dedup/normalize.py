"""engine/apaar_engine/dedup/normalize.py

Indian name normalisation and Indic-soundex phonetic encoding:
- Uppercase and punctuation stripping
- Honorifics removal (SHRI, SMT, KUMARI, DR, MR, MS, MD, MOHD, ER, PROF)
- Initials tokenization and token sorting for order invariance
- Indic-soundex phonetic encoding tailored for Indian naming phonology

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import re
from typing import List

# Common Indian honorifics and titles to strip from names
INDIAN_HONORIFICS = re.compile(
    r"^(shri|shree|sri|smt|shrimati|kumari|km|dr|mr|mrs|ms|md|mohd|mohammed|"
    r"er|prof|pandit|pt)\b\.?\s*",
    re.IGNORECASE,
)

# Common Indian name transliteration equivalences for canonicalization
TRANSLITERATION_MAP = {
    "BHAIROO": "BHERU",
    "BHAIRO": "BHERU",
    "KRUSHNA": "KRISHNA",
    "CHOUDHARY": "CHOWDHURY",
    "CHOUDHARI": "CHOWDHURY",
    "CHAUDHARY": "CHOWDHURY",
    "CHAUDHARI": "CHOWDHURY",
    "LAKSHMI": "LAXMI",
    "DIKSHA": "DEEKSHA",
    "VIKRAM": "BIKRAM",
    "PRASAD": "PARSHAD",
    "YADAV": "JADHAV",
}

# Indic soundex digraphs (checked before individual characters)
INDIC_DIGRAPHS = [
    ("BH", "1"),
    ("PH", "1"),
    ("CH", "2"),
    ("SH", "2"),
    ("KH", "2"),
    ("GH", "2"),
    ("JH", "2"),
    ("TH", "3"),
    ("DH", "3"),
    ("GN", "5"),
    ("NY", "5"),
]

# Indic single consonant mappings
# 1: Labials (B, P, V, W, F)
# 2: Velars, Palatals, Sibilants (C, G, J, K, Q, S, Z, X)
# 3: Dentals / Retroflex (D, T)
# 4: Liquids (L)
# 5: Nasals (M, N)
# 6: Rhotic (R)
INDIC_CHAR_MAP = {
    "B": "1",
    "P": "1",
    "V": "1",
    "W": "1",
    "F": "1",
    "C": "2",
    "G": "2",
    "J": "2",
    "K": "2",
    "Q": "2",
    "S": "2",
    "Z": "2",
    "X": "2",
    "D": "3",
    "T": "3",
    "L": "4",
    "M": "5",
    "N": "5",
    "R": "6",
}


def normalize_indian_name(name: str) -> str:
    """Normalize Indian person name.

    Steps:
    1. Strip leading/trailing whitespace and uppercase.
    2. Strip honorifics (e.g. SHRI, SMT, KUMARI, DR).
    3. Remove punctuation and non-alpha characters.
    4. Collapse spaces.
    """
    if not name:
        return ""

    text = name.strip()
    # Strip honorifics iteratively if stacked (e.g. "Dr. Smt. Kavya")
    while True:
        stripped = INDIAN_HONORIFICS.sub("", text).strip()
        if stripped == text:
            break
        text = stripped

    # Replace punctuation with spaces to cleanly separate initials like "A.K." -> "A K"
    text = re.sub(r"[^\w\s]", " ", text)
    # Remove digits
    text = re.sub(r"\d+", " ", text)
    # Collapse multiple whitespaces and convert to uppercase
    tokens = [t.upper() for t in text.split() if t.strip()]
    return " ".join(tokens)


def sorted_name_tokens(name: str) -> str:
    """Return alphabetically sorted tokens of a normalized name.

    Ensures order invariance e.g. "SHARMA KRISHNA" == "KRISHNA SHARMA".
    """
    norm = normalize_indian_name(name)
    if not norm:
        return ""
    tokens = sorted(norm.split())
    return " ".join(tokens)


def get_name_tokens(name: str) -> List[str]:
    """Get list of normalized name tokens."""
    norm = normalize_indian_name(name)
    return norm.split() if norm else []


def canonicalize_token(token: str) -> str:
    """Canonicalize common Indian transliteration variants."""
    clean = token.strip().upper()
    return TRANSLITERATION_MAP.get(clean, clean)


def indic_soundex(token: str, length: int = 4) -> str:
    """Compute Indic-soundex code for an Indian name token.

    Rules:
    - Retains the first letter in uppercase.
    - Encodes consonant groups according to Indic phonology.
    - Multi-character aspirated/sibilant digraphs (BH, SH, CH, etc.) mapped first.
    - Consecutive identical digits are collapsed.
    - Non-encoded letters / vowels (A, E, I, O, U, H, Y) dropped after the first letter.
    - Zero-padded to `length` characters.
    """
    clean = re.sub(r"[^A-Za-z]", "", token).upper()
    if not clean:
        return "0" * length

    first_letter = clean[0]
    tail = clean[1:]

    # Replace digraphs in tail
    for digraph, code in INDIC_DIGRAPHS:
        tail = tail.replace(digraph, code)

    # Replace remaining single letters
    coded_chars: List[str] = []
    for char in tail:
        if char in "123456":
            coded_chars.append(char)
        elif char in INDIC_CHAR_MAP:
            coded_chars.append(INDIC_CHAR_MAP[char])
        else:
            coded_chars.append("0")  # vowels, H, Y

    # Collapse consecutive duplicates
    collapsed: List[str] = []
    prev = INDIC_CHAR_MAP.get(first_letter, "0")
    for digit in coded_chars:
        if digit != prev:
            collapsed.append(digit)
            prev = digit

    # Filter out zeros (vowels)
    digits = [d for d in collapsed if d != "0"]

    # Assemble soundex code
    code_str = first_letter + "".join(digits)
    # Pad with zeros or truncate to length
    if len(code_str) < length:
        code_str = code_str.ljust(length, "0")
    else:
        code_str = code_str[:length]

    return code_str
