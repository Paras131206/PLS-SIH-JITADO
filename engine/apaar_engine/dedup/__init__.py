"""engine/apaar_engine/dedup package.

Indian name normalisation, intra-batch dedup (V009),
and cross-institution dedup (V010, V011).

Owned by Team A (Data & Intelligence).
"""

from apaar_engine.dedup.normalize import (
    indic_soundex,
    normalize_indian_name,
    sorted_name_tokens,
)

__all__ = [
    "indic_soundex",
    "normalize_indian_name",
    "sorted_name_tokens",
]
