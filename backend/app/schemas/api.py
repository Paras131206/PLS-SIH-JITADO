from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator
from uuid import UUID


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserProfile"


class RefreshRequest(BaseModel):
    refresh_token: str


class APIKeyCreate(BaseModel):
    name: str
    expires_days: int = 365


class APIKeyResponse(BaseModel):
    key: str
    prefix: str
    name: str
    expires_at: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: Literal["AICTE_ADMIN", "AICTE_ANALYST", "INSTITUTION_ADMIN", "INSTITUTION_STAFF", "VERIFIER", "STUDENT"]
    institution_aicte_id: Optional[str] = None


class Institution(BaseModel):
    id: str
    aicte_id: str
    name: str
    state: str
    is_active: bool = True


class InstitutionCreate(BaseModel):
    aicte_id: str
    name: str
    state: str


class ApiKeyCreated(BaseModel):
    id: str
    name: str
    prefix: str
    secret: str
    created_at: datetime


class Program(BaseModel):
    program_code: str
    program_name: str
    course_level: Literal["DIPLOMA", "UG", "PG", "PGDM", "PHD"]


class ProgramIntake(BaseModel):
    institution_aicte_id: str
    program_code: str
    academic_year: str
    approved_intake: int
    supernumerary_allowed: Optional[Dict[str, int]] = None
    approval_letter_ref: Optional[str] = None


class BatchStatus(BaseModel):
    batch_id: str
    institution_aicte_id: str
    status: Literal["UPLOADED", "VALIDATING", "VALIDATED", "REJECTED", "COMMITTED"]
    file_name: Optional[str] = None
    rows_total: Optional[int] = None
    created_at: datetime


class Issue(BaseModel):
    row: Optional[int] = None
    field: Optional[str] = None
    rule_id: str
    severity: Literal["ERROR", "WARN", "INFO"]
    message: str
    value_masked: Optional[str] = None


class IntakeSummaryItem(BaseModel):
    program_code: str
    approved: int
    enrolled: int
    supernumerary: int
    excess: int


class DuplicateCluster(BaseModel):
    cluster_id: str
    apaar_ids: List[str]
    score: float
    scope: Literal["INTRA", "CROSS_INSTITUTION"]


class Anomaly(BaseModel):
    anomaly_id: Optional[str] = None
    metric: str
    value: float
    baseline: float
    z: float
    reason: str


class BatchReport(BaseModel):
    batch_id: str
    institution_aicte_id: str
    rows_total: int
    rows_valid: int
    rows_warning: int
    rows_error: int
    quality_score: float
    metrics: Dict[str, Dict[str, float]]
    issues: List[Issue]
    intake_summary: List[IntakeSummaryItem]
    duplicate_clusters: List[DuplicateCluster]
    anomalies: List[Anomaly]


class StudentRecordMasked(BaseModel):
    apaar_id: str
    institution_aicte_id: str
    institution_student_id: str
    full_name: str
    dob: str
    gender: str
    category: str
    program_code: str
    course_level: str
    academic_year: str
    admission_date: str
    admission_type: str
    seat_type: str
    supernumerary_scheme: Optional[str] = None
    quota: str
    nationality: str
    enrolment_status: str
    consent_status: str
    email_masked: Optional[str] = None
    mobile_masked: Optional[str] = None


class DuplicateRecord(BaseModel):
    id: str
    scope: Literal["INTRA", "CROSS_INSTITUTION"]
    record_a: StudentRecordMasked
    record_b: StudentRecordMasked
    confidence_score: float
    status: Literal["PENDING", "RESOLVED"]
    decision: Optional[str] = None


class DuplicateResolveRequest(BaseModel):
    decision: Literal["SAME_PERSON", "DIFFERENT", "INSTITUTION_ERROR"]
    note: str


class ConsentRequest(BaseModel):
    apaar_id: str = Field(pattern=r"^[0-9]{12}$")
    purpose: Literal["REPOSITORY", "VERIFICATION_SHARE"]
    action: Literal["GRANT", "WITHDRAW"]


class ConsentRecord(BaseModel):
    id: str
    apaar_id: str
    purpose: Literal["REPOSITORY", "VERIFICATION_SHARE"]
    action: Literal["GRANT", "WITHDRAW"]
    timestamp: datetime


class CredentialIssueRequest(BaseModel):
    apaar_id: str
    institution_aicte_id: str
    academic_year: Optional[str] = None
    program_code: Optional[str] = None


class CredentialIssueResponse(BaseModel):
    credential_id: str
    sd_jwt: str
    qr_payload: str
    status_list_index: int


class StatusListResponse(BaseModel):
    status_list_credential: Dict[str, Any]


class VerifyRequest(BaseModel):
    presentation: str


class VerifyResponse(BaseModel):
    valid: bool
    issuer: str
    issued_at: datetime
    revoked: bool
    claims: Dict[str, Any]


class AuditLogEntry(BaseModel):
    id: str
    actor: str
    role: str
    action: str
    entity: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    prev_hash: str
    hash: str


class AuditChainStatus(BaseModel):
    verified: bool
    total_entries: int
    broken_link_id: Optional[str] = None
    broken_at_index: Optional[int] = None
    error: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    report_type: Literal["POLICY_SUMMARY", "INTAKE_QUOTA_AUDIT", "DQ_MONITORING"]
    format: Literal["PDF", "XLSX"]
    academic_year: Optional[str] = None
    state: Optional[str] = None


class ReportJobResponse(BaseModel):
    job_id: str
    status: str


class BatchUploadResponse(BaseModel):
    batch_id: str
    institution_aicte_id: str
    status: Literal["UPLOADED", "VALIDATING", "VALIDATED", "REJECTED", "COMMITTED"]
    file_name: str
    rows_total: int
    created_at: datetime


class CommitResponse(BaseModel):
    batch_id: str
    committed_records: int
    status: str


class StudentRecordUpdate(BaseModel):
    reason: str
    record: Dict[str, Any]


# Add the missing import
UserProfile.model_rebuild()