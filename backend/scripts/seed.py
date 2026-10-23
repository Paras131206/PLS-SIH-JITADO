import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path

from passlib.context import CryptContext

from app.db.session import SessionLocal, engine
from app.db.models import (
    Base,
    Institution,
    InstitutionType,
    User,
    Role,
    Program,
    ProgramIntake,
    CourseLevel,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

INTAKE_CSV = Path("data/synthetic/intake.csv")

INSTITUTIONS = [
    {
        "aicte_id": "1-10001",
        "name": "Government Engineering College, Delhi",
        "type": InstitutionType.GOVERNMENT,
        "state": "Delhi",
        "district": "New Delhi",
        "email": "admin@gec-delhi.ac.in",
        "phone": "011-23456789",
    },
    {
        "aicte_id": "1-10002",
        "name": "Private Institute of Technology, Mumbai",
        "type": InstitutionType.PRIVATE,
        "state": "Maharashtra",
        "district": "Mumbai",
        "email": "admin@pit-mumbai.ac.in",
        "phone": "022-23456789",
    },
    {
        "aicte_id": "1-10003",
        "name": "Deemed University of Science, Bangalore",
        "type": InstitutionType.DEEMED_UNIVERSITY,
        "state": "Karnataka",
        "district": "Bangalore Urban",
        "email": "admin@dus-bangalore.ac.in",
        "phone": "080-23456789",
    },
    {
        "aicte_id": "1-10004",
        "name": "Government Aided College, Chennai",
        "type": InstitutionType.GOVERNMENT_AIDED,
        "state": "Tamil Nadu",
        "district": "Chennai",
        "email": "admin@gac-chennai.ac.in",
        "phone": "044-23456789",
    },
    {
        "aicte_id": "1-10005",
        "name": "Private Engineering College, Kolkata",
        "type": InstitutionType.PRIVATE,
        "state": "West Bengal",
        "district": "Kolkata",
        "email": "admin@pec-kolkata.ac.in",
        "phone": "033-23456789",
    },
]

ADMIN_USERS = [
    {
        "email": "aictadmin@aicte.gov.in",
        "password": "Admin@12345",
        "full_name": "AICTE System Administrator",
        "role": Role.AICTE_ADMIN,
        "institution_aicte_id": None,
    },
    {
        "email": "admin@gec-delhi.ac.in",
        "password": "Admin@12345",
        "full_name": "GEC Delhi Admin",
        "role": Role.INSTITUTION_ADMIN,
        "institution_aicte_id": "1-10001",
    },
    {
        "email": "admin@pit-mumbai.ac.in",
        "password": "Admin@12345",
        "full_name": "PIT Mumbai Admin",
        "role": Role.INSTITUTION_ADMIN,
        "institution_aicte_id": "1-10002",
    },
    {
        "email": "admin@dus-bangalore.ac.in",
        "password": "Admin@12345",
        "full_name": "DUS Bangalore Admin",
        "role": Role.INSTITUTION_ADMIN,
        "institution_aicte_id": "1-10003",
    },
    {
        "email": "admin@gac-chennai.ac.in",
        "password": "Admin@12345",
        "full_name": "GAC Chennai Admin",
        "role": Role.INSTITUTION_ADMIN,
        "institution_aicte_id": "1-10004",
    },
    {
        "email": "admin@pec-kolkata.ac.in",
        "password": "Admin@12345",
        "full_name": "PEC Kolkata Admin",
        "role": Role.INSTITUTION_ADMIN,
        "institution_aicte_id": "1-10005",
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        for inst in INSTITUTIONS:
            existing = db.query(Institution).filter(Institution.aicte_id == inst["aicte_id"]).first()
            if existing:
                continue
            db.add(Institution(**inst))
        db.commit()

        for admin in ADMIN_USERS:
            existing = db.query(User).filter(User.email == admin["email"]).first()
            if existing:
                continue
            institution = None
            if admin["institution_aicte_id"]:
                institution = (
                    db.query(Institution)
                    .filter(Institution.aicte_id == admin["institution_aicte_id"])
                    .first()
                )
            db.add(
                User(
                    email=admin["email"],
                    password_hash=pwd_context.hash(admin["password"]),
                    full_name=admin["full_name"],
                    role=admin["role"],
                    institution_id=institution.id if institution else None,
                )
            )
        db.commit()

        with open(INTAKE_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                inst = db.query(Institution).filter(
                    Institution.aicte_id == row["institution_aicte_id"]
                ).first()
                if not inst:
                    continue

                program = (
                    db.query(Program)
                    .filter(
                        Program.institution_id == inst.id,
                        Program.code == row["program_code"],
                    )
                    .first()
                )
                if not program:
                    program = Program(
                        institution_id=inst.id,
                        code=row["program_code"],
                        name=f"{row['program_code']} Program",
                        course_level=CourseLevel.UG,
                    )
                    db.add(program)
                    db.flush()

                intake = (
                    db.query(ProgramIntake)
                    .filter(
                        ProgramIntake.program_id == program.id,
                        ProgramIntake.academic_year == row["academic_year"],
                    )
                    .first()
                )
                if not intake:
                    db.add(
                        ProgramIntake(
                            program_id=program.id,
                            academic_year=row["academic_year"],
                            approved_intake=int(row["approved_intake"]),
                            supernumerary_allowed=row["supernumerary_allowed"],
                            approval_letter_ref=row["approval_letter_ref"],
                        )
                    )

        db.commit()
        print("Seed completed successfully")
        print("AICTE Admin: aictadmin@aicte.gov.in / Admin@12345")
        print("Institution admins: admin@<institution>.ac.in / Admin@12345")

    finally:
        db.close()


if __name__ == "__main__":
    seed()