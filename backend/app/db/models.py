import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Role(str, enum.Enum):
    AICTE_ADMIN = "AICTE_ADMIN"
    AICTE_ANALYST = "AICTE_ANALYST"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    INSTITUTION_STAFF = "INSTITUTION_STAFF"
    VERIFIER = "VERIFIER"
    STUDENT = "STUDENT"


class InstitutionType(str, enum.Enum):
    GOVERNMENT = "GOVERNMENT"
    GOVERNMENT_AIDED = "GOVERNMENT_AIDED"
    PRIVATE = "PRIVATE"
    DEEMED_UNIVERSITY = "DEEMED_UNIVERSITY"


class ConsentStatus(str, enum.Enum):
    GRANTED = "GRANTED"
    REFUSED = "REFUSED"
    WITHDRAWN = "WITHDRAWN"


class EnrolmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"


class SeatType(str, enum.Enum):
    REGULAR = "REGULAR"
    SUPERNUMERARY = "SUPERNUMERARY"


class AdmissionType(str, enum.Enum):
    REGULAR = "REGULAR"
    LATERAL = "LATERAL"
    TRANSFER = "TRANSFER"


class Quota(str, enum.Enum):
    NONE = "NONE"
    NRI = "NRI"
    OCI = "OCI"
    FN = "FN"
    PIO = "PIO"
    CIWG = "CIWG"


class CourseLevel(str, enum.Enum):
    DIPLOMA = "DIPLOMA"
    UG = "UG"
    PG = "PG"
    PGDM = "PGDM"
    PHD = "PHD"


class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    T = "T"


class Category(str, enum.Enum):
    GEN = "GEN"
    EWS = "EWS"
    OBC_NCL = "OBC-NCL"
    SC = "SC"
    ST = "ST"


class SupernumeraryScheme(str, enum.Enum):
    TFW = "TFW"
    PMSSS = "PMSSS"
    JK = "JK"
    NE = "NE"
    FN_OCI_NRI = "FN_OCI_NRI"
    OTHER = "OTHER"


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aicte_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(InstitutionType), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100))
    address = Column(Text)
    email = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="institution")
    programs = relationship("Program", back_populates="institution")
    batches = relationship("Batch", back_populates="institution")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    institution = relationship("Institution", back_populates="users")
    api_keys = relationship("APIKey", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, index=True)
    prefix = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="api_keys")


class Program(Base):
    __tablename__ = "programs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    course_level = Column(SQLEnum(CourseLevel), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    institution = relationship("Institution", back_populates="programs")
    intakes = relationship("ProgramIntake", back_populates="program", cascade="all, delete-orphan")


class ProgramIntake(Base):
    __tablename__ = "program_intake"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_id = Column(String(36), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False, index=True)
    approved_intake = Column(Integer, nullable=False)
    supernumerary_allowed = Column(JSON, nullable=True)
    approval_letter_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    program = relationship("Program", back_populates="intakes")

    __table_args__ = (
        UniqueConstraint("program_id", "academic_year", name="uq_program_intake_year"),
    )


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    rows_total = Column(Integer, default=0)
    rows_valid = Column(Integer, default=0)
    rows_warning = Column(Integer, default=0)
    rows_error = Column(Integer, default=0)
    quality_score = Column(Integer, default=0)
    intake_summary = Column(JSON, nullable=True)
    duplicate_clusters = Column(JSON, nullable=True)
    anomalies = Column(JSON, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)

    institution = relationship("Institution", back_populates="batches")
    student_records = relationship("StudentRecord", back_populates="batch", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="batch", cascade="all, delete-orphan")


class StudentRecord(Base):
    __tablename__ = "student_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    apaar_id = Column(String(12), nullable=False, index=True)
    institution_aicte_id = Column(String(50), nullable=False)
    institution_student_id = Column(String(100), nullable=False)
    full_name = Column(String(255), nullable=False)
    name_norm = Column(String(255), nullable=False)
    dob = Column(DateTime(timezone=True), nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    category = Column(SQLEnum(Category), nullable=False)
    pwd = Column(Boolean, default=False)
    program_code = Column(String(50), nullable=False)
    course_level = Column(SQLEnum(CourseLevel), nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    admission_date = Column(DateTime(timezone=True), nullable=False)
    admission_type = Column(SQLEnum(AdmissionType), nullable=False)
    seat_type = Column(SQLEnum(SeatType), nullable=False)
    supernumerary_scheme = Column(SQLEnum(SupernumeraryScheme), nullable=True)
    quota = Column(SQLEnum(Quota), nullable=False)
    nationality = Column(String(2), nullable=False)
    nri_status = Column(Boolean, nullable=False)
    oci_status = Column(Boolean, nullable=False)
    fn_status = Column(Boolean, nullable=False)
    enrolment_status = Column(SQLEnum(EnrolmentStatus), nullable=False)
    consent_status = Column(SQLEnum(ConsentStatus), nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    guardian_consent = Column(Boolean, default=False)
    email_encrypted = Column(Text, nullable=True)
    mobile_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    batch = relationship("Batch", back_populates="student_records")
    issues = relationship("Issue", back_populates="student_record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_student_records_apaar_year", "apaar_id", "academic_year"),
        Index("ix_student_records_inst_student_year", "institution_aicte_id", "institution_student_id", "academic_year"),
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    student_record_id = Column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=True, index=True)
    row = Column(Integer, nullable=True)
    field = Column(String(100), nullable=True)
    rule_id = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    value_masked = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    batch = relationship("Batch", back_populates="issues")
    student_record = relationship("StudentRecord", back_populates="issues")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prev_hash = Column(String(64), nullable=True, index=True)
    hash = Column(String(64), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_audit_log_actor_time", "actor_type", "actor_id", "created_at"),
    )


class ConsentLedger(Base):
    __tablename__ = "consent_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apaar_id = Column(String(12), nullable=False, index=True)
    purpose = Column(String(100), nullable=False)
    status = Column(SQLEnum(ConsentStatus), nullable=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_consent_ledger_apaar_purpose", "apaar_id", "purpose"),
    )


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apaar_id = Column(String(12), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    vc_jwt = Column(Text, nullable=False)
    status = Column(String(20), default="active")
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class RevocationStatusList(Base):
    __tablename__ = "revocation_status_list"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False, unique=True)
    index = Column(Integer, nullable=False, unique=True)
    status = Column(String(20), default="valid")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MetricHistory(Base):
    __tablename__ = "metric_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_metric_history_inst_metric_time", "institution_id", "metric_name", "created_at"),
    )