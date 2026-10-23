#!/usr/bin/env python3
"""data/synthetic/generate.py

Synthetic test data generator for APAAR-SDMS.
Generates:
- 5 institutions
- 3 programs each with approved_intake
- 1,000 valid students with unique 12-digit APAAR IDs
- students.csv, intake.csv, registry.csv (mock APAAR registry), defects.json (empty for now)

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# Output directory relative to this script
OUTPUT_DIR = Path(__file__).resolve().parent

FIRST_NAMES_M = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharva", "Kabir", "Dhruv", "Rohan", "Vikram",
    "Aniket", "Pranav", "Rahul", "Samar", "Dev", "Alok", "Harsh", "Gaurav",
]

FIRST_NAMES_F = [
    "Saanvi", "Aanya", "Aadhya", "Aarohi", "Ananya", "Pari", "Diya", "Riya",
    "Myra", "Avani", "Isha", "Kavya", "Tanvi", "Neha", "Pooja", "Shreya",
    "Sneha", "Priya", "Meera", "Swati", "Divya", "Aditi", "Roshni", "Deepa",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Mishra", "Joshi",
    "Iyer", "Nair", "Reddy", "Rao", "Mukherjee", "Chatterjee", "Banerjee", "Das",
    "Chauhan", "Mehta", "Bhat", "Deshmukh", "Kulkarni", "Patil", "Agarwal", "Shah",
]

INSTITUTIONS = [
    {"id": "1-10001", "name": "National Institute of Technology Karnataka"},
    {"id": "1-10002", "name": "College of Engineering Pune"},
    {"id": "1-10003", "name": "Delhi Technological University"},
    {"id": "1-10004", "name": "PSG College of Technology Coimbatore"},
    {"id": "1-10005", "name": "Veermata Jijabai Technological Institute Mumbai"},
]

PROGRAMS = [
    {"code": "UG-CSE", "name": "Computer Science & Engineering", "approved_intake": 75},
    {"code": "UG-ECE", "name": "Electronics & Communication Engineering", "approved_intake": 75},
    {"code": "UG-MECH", "name": "Mechanical Engineering", "approved_intake": 65},
]

CATEGORIES = ["GEN", "OBC-NCL", "SC", "ST", "EWS"]
CATEGORY_WEIGHTS = [0.40, 0.27, 0.15, 0.08, 0.10]

ACADEMIC_YEAR = "2026-27"


def generate_apaar_id(existing_ids: set[str], rng: random.Random) -> str:
    """Generate a unique 12-digit numeric APAAR ID."""
    while True:
        # APAAR ID is exactly 12 digits, first digit non-zero
        val = str(rng.randint(1000_0000_0000, 9999_9999_9999))
        if val not in existing_ids:
            existing_ids.add(val)
            return val


def generate_dataset(
    num_students: int = 1000,
    seed: int = 42,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Generate synthetic students, program intake, registry, and defects."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Intake Data
    intake_records: list[dict[str, Any]] = []
    for inst in INSTITUTIONS:
        for prog in PROGRAMS:
            intake_records.append({
                "institution_aicte_id": inst["id"],
                "program_code": prog["code"],
                "academic_year": ACADEMIC_YEAR,
                "approved_intake": prog["approved_intake"],
                "supernumerary_allowed": json.dumps({"TFW": 5, "PMSSS": 5, "JK": 2}),
                "approval_letter_ref": f"AICTE/EOA/{ACADEMIC_YEAR}/{inst['id']}/{prog['code']}",
            })

    intake_csv_path = output_dir / "intake.csv"
    with open(intake_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "institution_aicte_id",
            "program_code",
            "academic_year",
            "approved_intake",
            "supernumerary_allowed",
            "approval_letter_ref",
        ])
        writer.writeheader()
        writer.writerows(intake_records)

    # 2. Distribute 1,000 students across 15 offerings (5 insts * 3 progs)
    # Total programs = 15. Base 66 students per program = 990. Remaining 10 distributed to first 10 programs.
    offerings = [(inst["id"], prog["code"], prog["approved_intake"]) for inst in INSTITUTIONS for prog in PROGRAMS]
    allocations = [num_students // len(offerings)] * len(offerings)
    for i in range(num_students % len(offerings)):
        allocations[i] += 1

    existing_apaar_ids: set[str] = set()
    students: list[dict[str, Any]] = []
    registry_records: list[dict[str, Any]] = []

    student_counter = 0

    for (inst_id, prog_code, approved_intake), count in zip(offerings, allocations):
        # We need to ensure regular seats <= approved_intake
        # Up to 4 supernumerary seats (TFW / PMSSS)
        supernumerary_quota = min(4, max(0, count - (approved_intake - 2)))
        regular_count = count - supernumerary_quota

        for idx in range(1, count + 1):
            student_counter += 1
            apaar = generate_apaar_id(existing_apaar_ids, rng)
            roll_number = f"{ACADEMIC_YEAR[:4]}-{prog_code.split('-')[1]}-{idx:04d}"

            # Gender & Name
            gender = rng.choices(["M", "F", "T"], weights=[0.55, 0.43, 0.02])[0]
            if gender == "M":
                first_name = rng.choice(FIRST_NAMES_M)
            elif gender == "F":
                first_name = rng.choice(FIRST_NAMES_F)
            else:
                first_name = rng.choice(FIRST_NAMES_M + FIRST_NAMES_F)
            last_name = rng.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"

            # DOB: between 2004-01-01 and 2008-08-01 (17 to 22 years old in 2026)
            start_date = date(2004, 1, 1)
            end_date = date(2008, 8, 1)
            days_range = (end_date - start_date).days
            dob = start_date + timedelta(days=rng.randint(0, days_range))

            # Admission date: July-August 2026
            adm_start = date(2026, 7, 1)
            adm_days = rng.randint(0, 55)
            admission_date = adm_start + timedelta(days=adm_days)

            # Age at admission date
            age_years = (admission_date - dob).days // 365
            is_minor = age_years < 18
            guardian_consent = True if is_minor else None

            # Category & PwD
            category = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
            pwd = rng.random() < 0.03

            # Seat type and supernumerary scheme
            is_supernumerary = idx > regular_count
            if is_supernumerary:
                seat_type = "SUPERNUMERARY"
                supernumerary_scheme = rng.choice(["TFW", "PMSSS"])
            else:
                seat_type = "REGULAR"
                supernumerary_scheme = ""

            # Quota and nationality
            # Keep clean & consistent
            nationality = "IN"
            quota = "NONE"
            nri_status = False
            oci_status = False
            fn_status = False

            # Small proportion of NRI students
            if not is_supernumerary and rng.random() < 0.02:
                quota = "NRI"
                nri_status = True

            # Consent
            consent_status = "GRANTED"
            consent_date = admission_date - timedelta(days=rng.randint(1, 15))

            # Email and Mobile
            clean_name = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{clean_name}{student_counter}@example.edu.in"
            mobile = f"{rng.choice(['9', '8', '7', '6'])}{rng.randint(100000000, 999999999)}"

            student_row = {
                "apaar_id": apaar,
                "institution_aicte_id": inst_id,
                "institution_student_id": roll_number,
                "full_name": full_name,
                "dob": dob.isoformat(),
                "gender": gender,
                "category": category,
                "pwd": str(pwd),
                "program_code": prog_code,
                "course_level": "UG",
                "academic_year": ACADEMIC_YEAR,
                "admission_date": admission_date.isoformat(),
                "admission_type": "REGULAR",
                "seat_type": seat_type,
                "supernumerary_scheme": supernumerary_scheme,
                "quota": quota,
                "nationality": nationality,
                "nri_status": str(nri_status),
                "oci_status": str(oci_status),
                "fn_status": str(fn_status),
                "enrolment_status": "ACTIVE",
                "consent_status": consent_status,
                "consent_date": consent_date.isoformat(),
                "guardian_consent": str(guardian_consent) if guardian_consent is not None else "",
                "email": email,
                "mobile": mobile,
            }
            students.append(student_row)

            # Registry row for mock APAAR registry
            registry_records.append({
                "apaar_id": apaar,
                "full_name": full_name,
                "dob": dob.isoformat(),
                "gender": gender,
            })

    # Write students.csv
    students_csv_path = output_dir / "students.csv"
    with open(students_csv_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "apaar_id", "institution_aicte_id", "institution_student_id", "full_name",
            "dob", "gender", "category", "pwd", "program_code", "course_level",
            "academic_year", "admission_date", "admission_type", "seat_type",
            "supernumerary_scheme", "quota", "nationality", "nri_status", "oci_status",
            "fn_status", "enrolment_status", "consent_status", "consent_date",
            "guardian_consent", "email", "mobile"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(students)

    # Write registry.csv (mock APAAR registry)
    registry_csv_path = output_dir / "registry.csv"
    with open(registry_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["apaar_id", "full_name", "dob", "gender"])
        writer.writeheader()
        writer.writerows(registry_records)

    # Write defects.json (empty for now)
    defects_json_path = output_dir / "defects.json"
    with open(defects_json_path, mode="w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

    print(f"Generated {len(students)} students across {len(INSTITUTIONS)} institutions into {output_dir}")


if __name__ == "__main__":
    generate_dataset()
