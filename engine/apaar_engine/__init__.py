"""apaar_engine — APAAR-SDMS Data & Intelligence Engine."""

from apaar_engine.anomaly.detect import detect_batch_anomalies
from apaar_engine.anomaly.metrics import BatchMetricState, compute_batch_metric_state
from apaar_engine.credentials.claims import (
    create_disclosure,
    create_presentation,
    from_student_record,
)
from apaar_engine.dedup.cross import detect_cross_duplicates
from apaar_engine.dedup.intra import detect_intra_duplicates
from apaar_engine.dedup.normalize import (
    indic_soundex,
    normalize_indian_name,
    sorted_name_tokens,
)
from apaar_engine.models import (
    AdmissionType,
    Anomaly,
    BatchReport,
    Category,
    ConsentStatus,
    CourseLevel,
    DuplicateCluster,
    DuplicateScope,
    EnrolmentStatus,
    Gender,
    IntakeSummary,
    Issue,
    ProgramIntake,
    Quota,
    SeatType,
    Severity,
    StudentRecord,
    SupernumeraryScheme,
    mask_apaar,
)
from apaar_engine.parser import parse_file
from apaar_engine.registry import MockApaarRegistry
from apaar_engine.reports.dq_report import export_dq_report_json, export_dq_report_xlsx
from apaar_engine.reports.policy_report import (
    DEFAULT_INSTITUTION_STATE_MAP,
    apply_small_cell_suppression,
    build_policy_aggregates,
    export_policy_report_xlsx,
)
from apaar_engine.validate import compute_batch_metrics, validate_batch

__all__ = [
    "DEFAULT_INSTITUTION_STATE_MAP",
    "AdmissionType",
    "Anomaly",
    "BatchMetricState",
    "BatchReport",
    "Category",
    "ConsentStatus",
    "CourseLevel",
    "DuplicateCluster",
    "DuplicateScope",
    "EnrolmentStatus",
    "Gender",
    "IntakeSummary",
    "Issue",
    "MockApaarRegistry",
    "ProgramIntake",
    "Quota",
    "SeatType",
    "Severity",
    "StudentRecord",
    "SupernumeraryScheme",
    "apply_small_cell_suppression",
    "build_policy_aggregates",
    "compute_batch_metric_state",
    "compute_batch_metrics",
    "create_disclosure",
    "create_presentation",
    "detect_batch_anomalies",
    "detect_cross_duplicates",
    "detect_intra_duplicates",
    "export_dq_report_json",
    "export_dq_report_xlsx",
    "export_policy_report_xlsx",
    "from_student_record",
    "indic_soundex",
    "mask_apaar",
    "normalize_indian_name",
    "parse_file",
    "sorted_name_tokens",
    "validate_batch",
]
