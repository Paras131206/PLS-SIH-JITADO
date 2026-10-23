from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_universal, require_roles
from app.db.session import get_db
from app.db.models import (
    Batch,
    Issue,
    Institution,
    Role,
)
from apaar_engine import validate_batch, parse_file

router = APIRouter(tags=["Batches"])


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("")
async def upload_batch(
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user = Depends(require_roles(Role.INSTITUTION_ADMIN, Role.INSTITUTION_STAFF, Role.AICTE_ADMIN)),
    db: Session = Depends(get_db),
):
    if idempotency_key:
        existing = db.query(Batch).filter(Batch.idempotency_key == idempotency_key).first()
        if existing:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "batch_id": str(existing.id),
                    "idempotency_key": existing.idempotency_key,
                    "status": existing.status,
                    "message": "Batch already processed",
                },
            )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 20 MB limit",
        )

    filename = file.filename or "upload"

    try:
        df = parse_file(content, filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}",
        )

    try:
        report = validate_batch(df)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )

    batch = Batch(
        institution_id=current_user.institution_id,
        filename=filename,
        file_size=len(content),
        rows_total=report.rows_total,
        rows_valid=report.rows_valid,
        rows_warning=report.rows_warning,
        rows_error=report.rows_error,
        quality_score=int(report.quality_score * 100),
        intake_summary=report.intake_summary,
        duplicate_clusters=report.duplicate_clusters,
        anomalies=report.anomalies,
        idempotency_key=idempotency_key,
        status="completed",
        processed_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    for issue in report.issues:
        db_issue = Issue(
            batch_id=batch.id,
            student_record_id=None,
            row=getattr(issue, "row", None),
            field=getattr(issue, "field", None),
            rule_id=getattr(issue, "rule_id", None),
            severity=getattr(issue, "severity", "ERROR"),
            message=getattr(issue, "message", ""),
            value_masked=getattr(issue, "value_masked", None),
        )
        db.add(db_issue)

    db.commit()
    db.refresh(batch)

    institution_aicte_id = current_user.institution.aicte_id if current_user.institution else None

    return {
        "batch_id": str(batch.id),
        "institution_aicte_id": institution_aicte_id,
        "filename": filename,
        "rows_total": report.rows_total,
        "rows_valid": report.rows_valid,
        "rows_warning": report.rows_warning,
        "rows_error": report.rows_error,
        "quality_score": report.quality_score,
        "status": batch.status,
        "processed_at": batch.processed_at.isoformat(),
    }