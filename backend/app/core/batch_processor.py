import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import hashlib

from app.db.models import (
    Batch, StudentRecord, Issue, AuditLog, Institution, 
    ProgramIntake, MetricHistory, ConsentLedger
)
from app.core.apaar_registry import get_apaar_registry
from app.core.encryption import get_field_encryption, mask_apaar
from app.core.config import settings

# Import the validation engine
try:
    from apaar_engine import validate_batch, BatchReport
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    BatchReport = None


def compute_audit_hash(prev_hash: Optional[str], payload: Dict[str, Any]) -> str:
    """Compute hash = sha256(prev_hash + payload) for audit chain."""
    prev = prev_hash or "0" * 64
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256((prev + payload_str).encode()).hexdigest()


def write_audit_log(
    db: Session,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Write an audit log entry with hash chain."""
    # Get the last hash
    last_entry = db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
    prev_hash = last_entry.hash if last_entry else None
    
    audit_payload = {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    entry_hash = compute_audit_hash(prev_hash, audit_payload)
    
    audit_entry = AuditLog(
        prev_hash=prev_hash,
        hash=entry_hash,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_entry)
    return audit_entry


async def process_batch_validation(batch_id: str, db: Session):
    """Background task to validate a batch using the apaar_engine."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return
    
    try:
        batch.status = "VALIDATING"
        db.commit()
        
        # Get institution and intake data
        institution = db.query(Institution).filter(Institution.id == batch.institution_id).first()
        if not institution:
            batch.status = "REJECTED"
            db.commit()
            return
        
        # Get program intakes for this institution and academic year
        intakes = db.query(ProgramIntake).join(ProgramIntake.program).filter(
            ProgramIntake.program.has(institution_id=institution.id),
            ProgramIntake.academic_year == batch.intake_summary.get("academic_year") if batch.intake_summary else ""
        ).all() if batch.intake_summary else []
        
        # For now, we'll simulate the engine validation
        # In real implementation, this would call apaar_engine.validate_batch()
        if ENGINE_AVAILABLE:
            # Read the uploaded file and process
            # This is a placeholder - real implementation would read the file
            report = BatchReport(
                batch_id=str(batch_id),
                institution_aicte_id=institution.aicte_id,
                rows_total=0,
                rows_valid=0,
                rows_warning=0,
                rows_error=0,
                quality_score=100.0,
                metrics={"completeness": {}, "uniqueness": {}},
                issues=[],
                intake_summary=[],
                duplicate_clusters=[],
                anomalies=[]
            )
        else:
            # Mock validation for demo
            report = {
                "batch_id": str(batch_id),
                "institution_aicte_id": institution.aicte_id,
                "rows_total": 100,
                "rows_valid": 95,
                "rows_warning": 3,
                "rows_error": 2,
                "quality_score": 95.0,
                "metrics": {
                    "completeness": {"apaar_id": 1.0, "full_name": 0.99, "dob": 0.98},
                    "uniqueness": {"apaar_id": 0.99, "institution_student_id": 1.0}
                },
                "issues": [
                    {"row": 5, "field": "apaar_id", "rule_id": "V002", "severity": "ERROR", "message": "Invalid APAAR ID format", "value_masked": "1234****5678"},
                    {"row": 12, "field": "quota", "rule_id": "V014", "severity": "ERROR", "message": "OCI quota with IN nationality", "value_masked": "OCI"},
                    {"row": 23, "field": "nri_status", "rule_id": "V014", "severity": "WARN", "message": "NRI flag mismatch with nationality", "value_masked": "true"},
                ],
                "intake_summary": [
                    {"program_code": "CS", "approved": 60, "enrolled": 63, "supernumerary": 4, "excess": 3}
                ],
                "duplicate_clusters": [
                    {"cluster_id": "cluster_1", "apaar_ids": ["123456789012", "123456789013"], "score": 0.92, "scope": "INTRA"}
                ],
                "anomalies": [
                    {"metric": "nri_share", "value": 0.15, "baseline": 0.05, "z": 3.2, "reason": "NRI share 3x baseline"}
                ]
            }
        
        # Update batch with validation results
        batch.rows_total = report["rows_total"]
        batch.rows_valid = report["rows_valid"]
        batch.rows_warning = report["rows_warning"]
        batch.rows_error = report["rows_error"]
        batch.quality_score = int(report["quality_score"])
        batch.intake_summary = report["intake_summary"]
        batch.duplicate_clusters = report["duplicate_clusters"]
        batch.anomalies = report["anomalies"]
        batch.status = "VALIDATED" if report["rows_error"] == 0 else "REJECTED"
        batch.processed_at = datetime.now(timezone.utc)
        
        # Store issues
        for issue_data in report["issues"]:
            issue = Issue(
                batch_id=batch.id,
                row=issue_data.get("row"),
                field=issue_data.get("field"),
                rule_id=issue_data["rule_id"],
                severity=issue_data["severity"],
                message=issue_data["message"],
                value_masked=issue_data.get("value_masked"),
            )
            db.add(issue)
        
        # Store metric history
        for metric_name, metric_data in report["metrics"].get("completeness", {}).items():
            mh = MetricHistory(
                institution_id=batch.institution_id,
                batch_id=batch.id,
                metric_name=f"completeness_{metric_name}",
                metric_value=str(metric_data),
            )
            db.add(mh)
        
        for metric_name, metric_data in report["metrics"].get("uniqueness", {}).items():
            mh = MetricHistory(
                institution_id=batch.institution_id,
                batch_id=batch.id,
                metric_name=f"uniqueness_{metric_name}",
                metric_value=str(metric_data),
            )
            db.add(mh)
        
        # Write audit log
        write_audit_log(
            db,
            actor_type="system",
            actor_id="batch_processor",
            action="batch.validated",
            resource_type="batch",
            resource_id=str(batch.id),
            payload={
                "batch_id": str(batch.id),
                "status": batch.status,
                "rows_total": batch.rows_total,
                "rows_valid": batch.rows_valid,
                "rows_error": batch.rows_error,
                "quality_score": batch.quality_score,
            }
        )
        
        db.commit()
        
    except Exception as e:
        batch.status = "REJECTED"
        db.commit()
        # Log error
        write_audit_log(
            db,
            actor_type="system",
            actor_id="batch_processor",
            action="batch.validation_failed",
            resource_type="batch",
            resource_id=str(batch.id),
            payload={"error": str(e)}
        )


def commit_batch_records(batch_id: str, db: Session) -> Dict[str, Any]:
    """Commit clean batch records to central repository."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch or batch.status != "VALIDATED":
        raise ValueError("Batch not found or not validated")
    
    # Get valid student records (those without ERROR issues)
    error_records = db.query(Issue.student_record_id).filter(
        Issue.batch_id == batch.id,
        Issue.severity == "ERROR"
    ).distinct().all()
    error_record_ids = {r[0] for r in error_records}
    
    # For this demo, we'll just mark the batch as committed
    # In reality, this would copy valid records to a central repository table
    batch.status = "COMMITTED"
    db.commit()
    
    # Write audit log
    write_audit_log(
        db,
        actor_type="system",
        actor_id="batch_processor",
        action="batch.committed",
        resource_type="batch",
        resource_id=str(batch.id),
        payload={"committed_records": batch.rows_valid}
    )
    
    return {
        "batch_id": str(batch.id),
        "committed_records": batch.rows_valid,
        "status": "COMMITTED"
    }