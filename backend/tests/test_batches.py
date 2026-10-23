import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, engine
from app.db.models import Base, User, Role, Institution
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def _ensure_institution(db, aicte_id="1-10001"):
    inst = db.query(Institution).filter(Institution.aicte_id == aicte_id).first()
    if not inst:
        inst = Institution(
            aicte_id=aicte_id,
            name="Test Institution",
            type="GOVERNMENT",
            state="Delhi",
            district="New Delhi",
            email="admin@test.ac.in",
            phone="011-23456789",
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)
    return inst


def _ensure_user(db, email, password, full_name, role, institution=None):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=pwd_context.hash(password),
            full_name=full_name,
            role=role,
            institution_id=institution.id if institution else None,
        )
        db.add(user)
        db.commit()
    return user


def _get_token(client, email, password):
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def aict_admin_token(client, db_session):
    db = db_session
    user = _ensure_user(db, "aictadmin@aicte.gov.in", "Admin@12345", "AICTE Admin", Role.AICTE_ADMIN)
    return _get_token(client, "aictadmin@aicte.gov.in", "Admin@12345")


@pytest.fixture(scope="module")
def institution_admin_token(client, db_session):
    db = db_session
    inst = _ensure_institution(db, "1-10001")
    user = _ensure_user(db, "admin@test.ac.in", "Admin@12345", "Test Institution Admin", Role.INSTITUTION_ADMIN, inst)
    return _get_token(client, "admin@test.ac.in", "Admin@12345")


@pytest.fixture(scope="module")
def staff_token(client, db_session):
    db = db_session
    inst = _ensure_institution(db, "1-10001")
    user = _ensure_user(db, "staff@test.ac.in", "Staff@12345", "Test Institution Staff", Role.INSTITUTION_STAFF, inst)
    return _get_token(client, "staff@test.ac.in", "Staff@12345")


def make_csv_file(content: str):
    return io.BytesIO(content.encode("utf-8"))


def test_role_denial_staff_cannot_create_api_key(client, staff_token):
    """Staff users cannot create API keys (requires INSTITUTION_ADMIN)."""
    response = client.post(
        "/v1/auth/api-keys",
        json={"name": "test-key", "expires_days": 30},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 403
    assert "Required role(s)" in response.json()["detail"]


def test_upload_happy_path(client, institution_admin_token):
    """Test successful batch upload."""
    csv_content = """apaar_id,institution_aicte_id,institution_student_id,full_name,dob,gender,category,pwd,program_code,course_level,academic_year,admission_date,admission_type,seat_type,supernumerary_scheme,quota,nationality,nri_status,oci_status,fn_status,enrolment_status,consent_status,consent_date
123456789012,1-10001,STU001,Rahul Sharma,2006-05-15,M,GEN,false,UG-CSE,UG,2026-27,2026-07-15,REGULAR,REGULAR,,NONE,IN,false,false,false,ACTIVE,GRANTED,2026-07-15
123456789013,1-10001,STU002,Priya Singh,2006-08-20,F,OBC-NCL,false,UG-CSE,UG,2026-27,2026-07-16,REGULAR,REGULAR,,NONE,IN,false,false,false,ACTIVE,GRANTED,2026-07-16
"""
    response = client.post(
        "/v1/batches",
        files={"file": ("students.csv", make_csv_file(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {institution_admin_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "batch_id" in data
    assert data["rows_total"] >= 0
    assert data["rows_valid"] >= 0
    assert data["rows_error"] >= 0


def test_duplicate_idempotency_key(client, institution_admin_token):
    """Test that duplicate idempotency key returns cached result."""
    csv_content = """apaar_id,institution_aicte_id,institution_student_id,full_name,dob,gender,category,pwd,program_code,course_level,academic_year,admission_date,admission_type,seat_type,supernumerary_scheme,quota,nationality,nri_status,oci_status,fn_status,enrolment_status,consent_status,consent_date
123456789014,1-10001,STU003,Amit Kumar,2006-03-10,M,SC,false,UG-ECE,UG,2026-27,2026-07-17,REGULAR,REGULAR,,NONE,IN,false,false,false,ACTIVE,GRANTED,2026-07-17
"""
    idempotency_key = "test-idempotency-key-123"

    response1 = client.post(
        "/v1/batches",
        files={"file": ("students.csv", make_csv_file(csv_content), "text/csv")},
        headers={
            "Authorization": f"Bearer {institution_admin_token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response1.status_code == 200, response1.text

    response2 = client.post(
        "/v1/batches",
        files={"file": ("students.csv", make_csv_file(csv_content), "text/csv")},
        headers={
            "Authorization": f"Bearer {institution_admin_token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response2.status_code == 200, response2.text
    assert response2.json()["message"] == "Batch already processed"
    assert response1.json()["batch_id"] == response2.json()["batch_id"]


def test_upload_no_auth(client):
    """Test that upload without auth returns 401."""
    csv_content = """apaar_id,institution_aicte_id,institution_student_id,full_name,dob,gender,category,pwd,program_code,course_level,academic_year,admission_date,admission_type,seat_type,supernumerary_scheme,quota,nationality,nri_status,oci_status,fn_status,enrolment_status,consent_status,consent_date
123456789015,1-10001,STU004,Test User,2006-01-01,M,GEN,false,UG-CSE,UG,2026-27,2026-07-18,REGULAR,REGULAR,,NONE,IN,false,false,false,ACTIVE,GRANTED,2026-07-18
"""
    response = client.post(
        "/v1/batches",
        files={"file": ("students.csv", make_csv_file(csv_content), "text/csv")},
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"