"""apaar_engine — APAAR-SDMS Data & Intelligence Engine."""

from apaar_engine.anomaly.detect import detect_batch_anomalies
from apaar_engine.anomaly.metrics import BatchMetricState, compute_batch_metric_state
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
from apaar_engine.validate import compute_batch_metrics, validate_batch

__all__ = [
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
    "compute_batch_metric_state",
    "compute_batch_metrics",
    "detect_batch_anomalies",
    "detect_cross_duplicates",
    "detect_intra_duplicates",
    "export_dq_report_json",
    "export_dq_report_xlsx",
    "indic_soundex",
    "mask_apaar",
    "normalize_indian_name",
    "parse_file",
    "sorted_name_tokens",
    "validate_batch",
]
