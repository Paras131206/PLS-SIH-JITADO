"""engine/apaar_engine/dedup/intra.py

V009: Intra-batch duplicate detection.
- Blocks on (soundex of first token, dob year) and (dob, gender).
- Scores candidate pairs using Jaro-Winkler, token_set_ratio, and exact DOB.
- Clusters pairs:
  - score >= 0.92: FLAG (V009 warning issues + duplicate cluster)
  - 0.75 <= score < 0.92: REVIEW (duplicate cluster for analyst review)

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple
from uuid import uuid4

import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from apaar_engine.dedup.normalize import (
    canonicalize_token,
    get_name_tokens,
    indic_soundex,
    normalize_indian_name,
)
from apaar_engine.models import DuplicateCluster, DuplicateScope, Issue, Severity, mask_apaar


def check_initials_match(tokens1: List[str], tokens2: List[str]) -> float:
    """Check if one token sequence is an initialism of the other with matching surname."""
    if len(tokens1) < 2 or len(tokens2) < 2:
        return 0.0
    if tokens1[-1] != tokens2[-1]:
        return 0.0

    l1 = tokens1[:-1]
    l2 = tokens2[:-1]
    if all(len(t) == 1 for t in l1):
        short_lead, long_lead = l1, l2
    elif all(len(t) == 1 for t in l2):
        short_lead, long_lead = l2, l1
    else:
        return 0.0

    if len(short_lead) == len(long_lead) and all(
        long_lead[i].startswith(short_lead[i]) for i in range(len(short_lead))
    ):
        return 0.95
    return 0.0


def score_pair(
    name1: str,
    name2: str,
    dob1: str,
    dob2: str,
) -> float:
    """Score similarity between two student identity records.

    Uses Jaro-Winkler on normalized and sorted tokens, token_set_ratio, and exact DOB.
    """
    d1_clean = str(dob1).strip()
    d2_clean = str(dob2).strip()
    # Must have exact DOB match for duplicate person determination
    if not d1_clean or not d2_clean or d1_clean != d2_clean:
        return 0.0

    n1 = normalize_indian_name(name1)
    n2 = normalize_indian_name(name2)
    t1 = [canonicalize_token(t) for t in n1.split()]
    t2 = [canonicalize_token(t) for t in n2.split()]
    if not t1 or not t2:
        return 0.0

    s1, s2 = t1[-1], t2[-1]
    same_surname = (s1 == s2) or (JaroWinkler.similarity(s1, s2) >= 0.85)
    is_permutation = set(t1) == set(t2)
    has_surname_in_other = (s1 in t2[:-1]) or (s2 in t1[:-1])

    # If surnames are completely different and not permuted/contained, not duplicate person
    if not (same_surname or is_permutation or has_surname_in_other):
        return 0.50

    # Forename check: ensure forenames are not completely distinct (e.g. siblings)
    f1 = " ".join(t1[:-1])
    f2 = " ".join(t2[:-1])
    init_score = check_initials_match(t1, t2)
    if f1 and f2:
        fore_jw = JaroWinkler.similarity(f1, f2)
        fore_tsr = fuzz.token_set_ratio(f1, f2) / 100.0
        fore_sim = max(fore_jw, fore_tsr, init_score)
        if fore_sim < 0.70 and not is_permutation and not has_surname_in_other:
            return 0.50

    n1_canon = " ".join(t1)
    n2_canon = " ".join(t2)
    s1_canon = " ".join(sorted(t1))
    s2_canon = " ".join(sorted(t2))

    # 1. Name metrics
    jw_raw = JaroWinkler.similarity(n1, n2)
    jw_sorted = JaroWinkler.similarity(s1_canon, s2_canon)
    jw_canon = JaroWinkler.similarity(n1_canon, n2_canon)
    tsr = fuzz.token_set_ratio(n1, n2) / 100.0

    name_score = max(
        jw_raw,
        jw_sorted,
        jw_canon,
        tsr,
        init_score,
        (0.6 * max(jw_raw, jw_sorted, jw_canon) + 0.4 * tsr),
    )

    # Exact DOB is 1.0
    composite = 0.70 * name_score + 0.30 * 1.0
    return round(float(composite), 4)


def detect_intra_duplicates(
    df: pd.DataFrame,
    flag_threshold: float = 0.92,
    review_threshold: float = 0.75,
) -> Tuple[List[Issue], List[DuplicateCluster]]:
    """Detect probable intra-batch duplicate persons under different APAAR IDs (V009)."""
    issues: List[Issue] = []
    clusters: List[DuplicateCluster] = []

    required_cols = ["apaar_id", "full_name", "dob", "gender"]
    if not all(c in df.columns for c in required_cols) or len(df) < 2:
        return issues, clusters

    row_nums = (
        df["_row_num"].tolist() if "_row_num" in df.columns else [idx + 2 for idx in range(len(df))]
    )
    apaars = df["apaar_id"].fillna("").astype(str).str.strip().tolist()
    names = df["full_name"].fillna("").astype(str).str.strip().tolist()
    dobs = df["dob"].fillna("").astype(str).str.strip().tolist()
    genders = df["gender"].fillna("").astype(str).str.strip().str.upper().tolist()

    # Build blocking dictionaries
    # Block 1: (soundex of first token, dob year)
    block_soundex_year: Dict[Tuple[str, str], List[int]] = {}
    # Block 2: (dob, gender)
    block_dob_gender: Dict[Tuple[str, str], List[int]] = {}

    for idx, (name, dob, gender) in enumerate(zip(names, dobs, genders)):
        tokens = get_name_tokens(name)
        first_token = tokens[0] if tokens else ""
        sndx = indic_soundex(first_token) if first_token else "0000"
        year = dob[:4] if len(dob) >= 4 and dob[:4].isdigit() else "0000"

        if sndx != "0000" and year != "0000":
            key1 = (sndx, year)
            block_soundex_year.setdefault(key1, []).append(idx)

        if dob and gender:
            key2 = (dob, gender)
            block_dob_gender.setdefault(key2, []).append(idx)

    # Collect candidate index pairs (i < j)
    candidate_pairs: Set[Tuple[int, int]] = set()

    for indices in block_soundex_year.values():
        if len(indices) > 1:
            for i_pos in range(len(indices)):
                for j_pos in range(i_pos + 1, len(indices)):
                    candidate_pairs.add((indices[i_pos], indices[j_pos]))

    for indices in block_dob_gender.values():
        if len(indices) > 1:
            for i_pos in range(len(indices)):
                for j_pos in range(i_pos + 1, len(indices)):
                    candidate_pairs.add((indices[i_pos], indices[j_pos]))

    # Score candidates and filter out identical apaar_ids (handled by V007)
    flagged_rows: Set[int] = set()

    for i, j in sorted(candidate_pairs):
        apaar_i, apaar_j = apaars[i], apaars[j]
        if apaar_i and apaar_j and apaar_i == apaar_j:
            # Same APAAR duplicate within batch is V007, not V009
            continue

        score = score_pair(names[i], names[j], dobs[i], dobs[j])

        if score >= review_threshold:
            status = "FLAG" if score >= flag_threshold else "REVIEW"
            cluster_id = f"intra-{uuid4().hex[:8]}"

            cluster = DuplicateCluster(
                cluster_id=cluster_id,
                apaar_ids=[apaar_i, apaar_j],
                score=score,
                scope=DuplicateScope.INTRA,
                evidence={
                    "status": status,
                    "row_1": row_nums[i],
                    "row_2": row_nums[j],
                    "name_1": names[i],
                    "name_2": names[j],
                    "dob_1": dobs[i],
                    "dob_2": dobs[j],
                    "gender_1": genders[i],
                    "gender_2": genders[j],
                    "score": score,
                },
            )
            clusters.append(cluster)

            if score >= flag_threshold:
                # Add V009 issue for row i (if not already added for this rule)
                if row_nums[i] not in flagged_rows:
                    flagged_rows.add(row_nums[i])
                    issues.append(
                        Issue(
                            row=row_nums[i],
                            field="full_name",
                            rule_id="V009",
                            severity=Severity.WARN,
                            message=(
                                f"Probable duplicate person in batch under different APAAR "
                                f"'{mask_apaar(apaar_j)}' (row {row_nums[j]}: '{names[j]}', "
                                f"DOB {dobs[j]}, match score {score:.2f})"
                            ),
                            value_masked=mask_apaar(apaar_i),
                        )
                    )

                # Add V009 issue for row j
                if row_nums[j] not in flagged_rows:
                    flagged_rows.add(row_nums[j])
                    issues.append(
                        Issue(
                            row=row_nums[j],
                            field="full_name",
                            rule_id="V009",
                            severity=Severity.WARN,
                            message=(
                                f"Probable duplicate person in batch under different APAAR "
                                f"'{mask_apaar(apaar_i)}' (row {row_nums[i]}: '{names[i]}', "
                                f"DOB {dobs[i]}, match score {score:.2f})"
                            ),
                            value_masked=mask_apaar(apaar_j),
                        )
                    )

    return issues, clusters
