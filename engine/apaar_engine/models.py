"""engine/apaar_engine/models.py

Pydantic v2 models for APAAR-SDMS matching agents.md §5.
Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def mask_apaar(apaar_id: Optional[str]) -> str:
    """Mask a 12-digit APAAR ID showing first 4 and last 4 digits (e.g., 1234****9012).

    Adheres to agents.md §8 rule 6: Never log raw APAAR IDs or PII.
    """
    if not apaar_id:
        return ""
    clean = str(apaar_id).strip()
    if len(clean) == 12:
        return f"{clean[:4]}****{clean[8:]}"
    if len(clean) > 4:
        return f"{clean[:2]}****{clean[-2:]}"
    return "****"


# ---------------------------------------------------------------------------
# Enums defined in agents.md §5.1
# ---------------------------------------------------------------------------


class Gender(str, Enum):
    M = "M"
    F = "F"
    T = "T"


class Category(str, Enum):
    GEN = "GEN"
    EWS = "EWS"
    OBC_NCL = "OBC-NCL"
    SC = "SC"
    ST = "ST"


class CourseLevel(str, Enum):
    DIPLOMA = "DIPLOMA"
    UG = "UG"
    PG = "PG"
    PGDM = "PGDM"
    PHD = "PHD"


class AdmissionType(str, Enum):
    REGULAR = "REGULAR"
    LATERAL = "LATERAL"
    TRANSFER = "TRANSFER"


class SeatType(str, Enum):
    REGULAR = "REGULAR"
    SUPERNUMERARY = "SUPERNUMERARY"


class SupernumeraryScheme(str, Enum):
    TFW = "TFW"
    PMSSS = "PMSSS"
    JK = "JK"
    NE = "NE"
    FN_OCI_NRI = "FN_OCI_NRI"
    OTHER = "OTHER"


class Quota(str, Enum):
    NONE = "NONE"
    NRI = "NRI"
    OCI = "OCI"
    FN = "FN"
    PIO = "PIO"
    CIWG = "CIWG"


class EnrolmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"


class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    REFUSED = "REFUSED"
    WITHDRAWN = "WITHDRAWN"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


class DuplicateScope(str, Enum):
    INTRA = "INTRA"
    CROSS_INSTITUTION = "CROSS_INSTITUTION"


# ---------------------------------------------------------------------------
# 5.1 StudentRecord
# ---------------------------------------------------------------------------


class StudentRecord(BaseModel):
    """Canonical student record model matching agents.md §5.1.

    Represents one row per student per program per academic year.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    apaar_id: str = Field(..., description="Exactly 12 digits")
    institution_aicte_id: str = Field(..., description="Must match the uploader's institution")
    institution_student_id: str = Field(
        ..., description="Roll/enrolment number; unique within institution + year"
    )
    full_name: str = Field(..., description="Student full name")
    name_norm: Optional[str] = Field(
        default=None, description="Normalised copy stored in name_norm"
    )
    dob: date = Field(..., description="Date of birth YYYY-MM-DD")
    gender: Gender = Field(..., description="Gender (M/F/T)")
    category: Category = Field(..., description="Category (GEN/EWS/OBC-NCL/SC/ST)")
    pwd: bool = Field(default=False, description="Person with disability flag")
    program_code: str = Field(..., description="Must exist in program_intake")
    course_level: CourseLevel = Field(..., description="DIPLOMA/UG/PG/PGDM/PHD")
    academic_year: str = Field(..., description="Academic year, e.g. '2026-27'")
    admission_date: date = Field(..., description="Admission date YYYY-MM-DD")
    admission_type: AdmissionType = Field(..., description="REGULAR/LATERAL/TRANSFER")
    seat_type: SeatType = Field(..., description="REGULAR/SUPERNUMERARY")
    supernumerary_scheme: Optional[SupernumeraryScheme] = Field(
        default=None,
        description="Scheme if seat_type is SUPERNUMERARY (TFW/PMSSS/JK/NE/FN_OCI_NRI/OTHER/null)",
    )
    quota: Quota = Field(..., description="Quota (NONE/NRI/OCI/FN/PIO/CIWG)")
    nationality: str = Field(default="IN", description="ISO-3166 alpha-2 code")
    nri_status: bool = Field(default=False, description="Consistent with quota and nationality")
    oci_status: bool = Field(default=False, description="OCI status")
    fn_status: bool = Field(default=False, description="Foreign national status")
    enrolment_status: EnrolmentStatus = Field(
        default=EnrolmentStatus.ACTIVE,
        description="ACTIVE/WITHDRAWN/DEFERRED/COMPLETED",
    )
    consent_status: ConsentStatus = Field(..., description="GRANTED/REFUSED/WITHDRAWN")
    consent_date: Optional[date] = Field(default=None, description="Date consent granted")
    guardian_consent: Optional[bool] = Field(default=None, description="Required if age < 18")
    email: Optional[str] = Field(default=None, description="Email address (masked/encrypted in DB)")
    mobile: Optional[str] = Field(
        default=None, description="Mobile number (masked/encrypted in DB)"
    )

    @field_validator(
        "supernumerary_scheme",
        "consent_date",
        "guardian_consent",
        "email",
        "mobile",
        "name_norm",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v

    @field_validator("pwd", "nri_status", "oci_status", "fn_status", mode="before")
    @classmethod
    def parse_bool(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("true", "1", "yes", "t", "y"):
                return True
            if clean in ("false", "0", "no", "f", "n", ""):
                return False
        return v

    @field_validator("guardian_consent", mode="before")
    @classmethod
    def parse_optional_bool(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("true", "1", "yes", "t", "y"):
                return True
            if clean in ("false", "0", "no", "f", "n"):
                return False
        return v

    @property
    def apaar_masked(self) -> str:
        return mask_apaar(self.apaar_id)


# ---------------------------------------------------------------------------
# 5.2 ProgramIntake
# ---------------------------------------------------------------------------


class ProgramIntake(BaseModel):
    """Program intake model matching agents.md §5.2."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    institution_aicte_id: str = Field(..., description="Institution AICTE ID")
    program_code: str = Field(..., description="Program Code e.g. CSE, ECE")
    academic_year: str = Field(..., description="Academic year e.g. 2026-27")
    approved_intake: int = Field(..., ge=0, description="Approved intake limit")
    supernumerary_allowed: Dict[str, int] = Field(
        default_factory=dict,
        description="Allowed supernumerary seats per scheme",
    )
    approval_letter_ref: str = Field(..., description="Reference number of AICTE approval letter")

    @field_validator("supernumerary_allowed", mode="before")
    @classmethod
    def parse_supernumerary_allowed(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                return {}
            try:
                return json.loads(clean)
            except json.JSONDecodeError:
                return {}
        if isinstance(v, dict):
            return {str(k): int(val) for k, val in v.items()}
        return v or {}


# ---------------------------------------------------------------------------
# 5.3 BatchReport and sub-models
# ---------------------------------------------------------------------------


class Issue(BaseModel):
    """Validation issue model matching agents.md §5.3."""

    row: Optional[int] = Field(default=None, description="CSV row number (1-indexed)")
    field: Optional[str] = Field(default=None, description="Field or column name")
    rule_id: str = Field(..., description="Rule catalog ID e.g. V002")
    severity: Severity = Field(..., description="ERROR, WARN, or INFO")
    message: str = Field(..., description="Human-readable issue description")
    value_masked: Optional[str] = Field(default=None, description="Masked field value")


class IntakeSummary(BaseModel):
    """Intake summary element per program code matching agents.md §5.3."""

    program_code: str = Field(...)
    approved: int = Field(..., ge=0)
    enrolled: int = Field(..., ge=0)
    supernumerary: int = Field(..., ge=0)
    excess: int = Field(default=0, description="Enrolled regular beyond approved intake")
    enrolled_regular: int = Field(default=0, description="Regular enrolled students")
    supernumerary_by_scheme: Dict[str, int] = Field(
        default_factory=dict, description="Supernumerary enrolments per scheme"
    )


class DuplicateCluster(BaseModel):
    """Duplicate cluster matching agents.md §5.3."""

    cluster_id: str = Field(...)
    apaar_ids: List[str] = Field(default_factory=list)
    score: float = Field(..., ge=0.0, le=1.0)
    scope: DuplicateScope = Field(...)


class Anomaly(BaseModel):
    """Anomaly detection item matching agents.md §5.3."""

    metric: str = Field(..., description="e.g. nri_share, intake_fill_jump")
    value: float = Field(...)
    baseline: float = Field(...)
    z: float = Field(...)
    reason: str = Field(...)


class BatchReport(BaseModel):
    """Complete batch validation report matching agents.md §5.3."""

    batch_id: str = Field(..., description="Batch UUID")
    institution_aicte_id: str = Field(...)
    rows_total: int = Field(default=0, ge=0)
    rows_valid: int = Field(default=0, ge=0)
    rows_warning: int = Field(default=0, ge=0)
    rows_error: int = Field(default=0, ge=0)
    quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="e.g. {'completeness': {'col': 0.99}, 'uniqueness': {'apaar_id': 1.0}}",
    )
    issues: List[Issue] = Field(default_factory=list)
    intake_summary: List[IntakeSummary] = Field(default_factory=list)
    duplicate_clusters: List[DuplicateCluster] = Field(default_factory=list)
    anomalies: List[Anomaly] = Field(default_factory=list)
