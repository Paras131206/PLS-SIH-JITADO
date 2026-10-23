#!/usr/bin/env python3
"""data/synthetic/generate.py

Synthetic test data generator for APAAR-SDMS.
Generates:
- 5 institutions, 3 programs each with approved_intake
- 1,000 valid students with unique 12-digit APAAR IDs (students.csv, intake.csv, registry.csv)
- Synthetic dataset with injected defects (students_with_defects.csv)
- Ground-truth defect annotations (defects.json)

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).resolve().parent

FIRST_NAMES_M = [
    "Aarav",
    "Vivaan",
    "Aditya",
    "Vihaan",
    "Arjun",
    "Sai",
    "Reyansh",
    "Ayaan",
    "Krishna",
    "Ishaan",
    "Shaurya",
    "Atharva",
    "Kabir",
    "Dhruv",
    "Rohan",
    "Vikram",
    "Aniket",
    "Pranav",
    "Rahul",
    "Samar",
    "Dev",
    "Alok",
    "Harsh",
    "Gaurav",
]

FIRST_NAMES_F = [
    "Saanvi",
    "Aanya",
    "Aadhya",
    "Aarohi",
    "Ananya",
    "Pari",
    "Diya",
    "Riya",
    "Myra",
    "Avani",
    "Isha",
    "Kavya",
    "Tanvi",
    "Neha",
    "Pooja",
    "Shreya",
    "Sneha",
    "Priya",
    "Meera",
    "Swati",
    "Divya",
    "Aditi",
    "Roshni",
    "Deepa",
]

LAST_NAMES = [
    "Sharma",
    "Verma",
    "Patel",
    "Gupta",
    "Singh",
    "Kumar",
    "Mishra",
    "Joshi",
    "Iyer",
    "Nair",
    "Reddy",
    "Rao",
    "Mukherjee",
    "Chatterjee",
    "Banerjee",
    "Das",
    "Chauhan",
    "Mehta",
    "Bhat",
    "Deshmukh",
    "Kulkarni",
    "Patil",
    "Agarwal",
    "Shah",
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
    {
        "code": "UG-ECE",
        "name": "Electronics & Communication Engineering",
        "approved_intake": 75,
    },
    {"code": "UG-MECH", "name": "Mechanical Engineering", "approved_intake": 65},
]

CATEGORIES = ["GEN", "OBC-NCL", "SC", "ST", "EWS"]
CATEGORY_WEIGHTS = [0.40, 0.27, 0.15, 0.08, 0.10]

ACADEMIC_YEAR = "2026-27"


def generate_apaar_id(existing_ids: set[str], rng: random.Random) -> str:
    """Generate a unique 12-digit numeric APAAR ID."""
    while True:
        val = str(rng.randint(1000_0000_0000, 9999_9999_9999))
        if val not in existing_ids:
            existing_ids.add(val)
            return val


def generate_clean_dataset(
    num_students: int = 1000,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate clean synthetic student, intake, and registry records."""
    rng = random.Random(seed)

    # 1. Intake Data
    intake_records: list[dict[str, Any]] = []
    for inst in INSTITUTIONS:
        for prog in PROGRAMS:
            intake_records.append(
                {
                    "institution_aicte_id": inst["id"],
                    "program_code": prog["code"],
                    "academic_year": ACADEMIC_YEAR,
                    "approved_intake": prog["approved_intake"],
                    "supernumerary_allowed": json.dumps(
                        {"TFW": 5, "PMSSS": 5, "JK": 2}
                    ),
                    "approval_letter_ref": f"AICTE/EOA/{ACADEMIC_YEAR}/{inst['id']}/{prog['code']}",
                }
            )

    # 2. Student allocations
    offerings = [
        (inst["id"], prog["code"], prog["approved_intake"])
        for inst in INSTITUTIONS
        for prog in PROGRAMS
    ]
    allocations = [num_students // len(offerings)] * len(offerings)
    for i in range(num_students % len(offerings)):
        allocations[i] += 1

    existing_apaar_ids: set[str] = set()
    existing_identities: set[tuple[str, str]] = set()
    students: list[dict[str, Any]] = []
    registry_records: list[dict[str, Any]] = []
    student_counter = 0

    for (inst_id, prog_code, approved_intake), count in zip(offerings, allocations):
        supernumerary_quota = min(4, max(0, count - (approved_intake - 2)))
        regular_count = count - supernumerary_quota

        for idx in range(1, count + 1):
            student_counter += 1
            apaar = generate_apaar_id(existing_apaar_ids, rng)
            roll_number = f"{ACADEMIC_YEAR[:4]}-{prog_code.split('-')[1]}-{idx:04d}"

            gender = rng.choices(["M", "F", "T"], weights=[0.55, 0.43, 0.02])[0]
            if gender == "M":
                first_name = rng.choice(FIRST_NAMES_M)
            elif gender == "F":
                first_name = rng.choice(FIRST_NAMES_F)
            else:
                first_name = rng.choice(FIRST_NAMES_M + FIRST_NAMES_F)
            last_name = rng.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"

            if (
                student_counter == 249
            ):  # Row 250 (idx 248) -> age 18, adult for UG, too young for PHD
                dob = date(2008, 7, 1)
                admission_date = date(2026, 7, 15)
                age_years = 18
                is_minor = False
                guardian_consent = None
            elif (
                student_counter == 279
            ):  # Row 280 (idx 278) -> age 17, minor with guardian consent
                dob = date(2008, 7, 25)
                admission_date = date(2026, 7, 1)
                age_years = 17
                is_minor = True
                guardian_consent = True
            else:
                start_date = date(2004, 1, 1)
                end_date = date(2008, 8, 1)
                days_range = (end_date - start_date).days
                dob = start_date + timedelta(days=rng.randint(0, days_range))
                while (full_name, dob.isoformat()) in existing_identities:
                    dob = start_date + timedelta(days=rng.randint(0, days_range))

                adm_start = date(2026, 7, 1)
                adm_days = rng.randint(0, 55)
                admission_date = adm_start + timedelta(days=adm_days)

                age_years = (admission_date - dob).days // 365
                is_minor = age_years < 18
                guardian_consent = True if is_minor else None

            existing_identities.add((full_name, dob.isoformat()))

            category = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
            pwd = rng.random() < 0.03

            is_supernumerary = idx > regular_count
            if is_supernumerary:
                seat_type = "SUPERNUMERARY"
                supernumerary_scheme = rng.choice(["TFW", "PMSSS"])
            else:
                seat_type = "REGULAR"
                supernumerary_scheme = ""

            nationality = "IN"
            quota = "NONE"
            nri_status = False
            oci_status = False
            fn_status = False

            if not is_supernumerary and rng.random() < 0.02:
                quota = "NRI"
                nri_status = True

            consent_status = "GRANTED"
            consent_date = admission_date - timedelta(days=rng.randint(1, 15))

            clean_name = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{clean_name}{student_counter}@example.edu.in"
            mobile = (
                f"{rng.choice(['9', '8', '7', '6'])}{rng.randint(100000000, 999999999)}"
            )

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
                "guardian_consent": str(guardian_consent)
                if guardian_consent is not None
                else "",
                "email": email,
                "mobile": mobile,
            }
            students.append(student_row)

            registry_records.append(
                {
                    "apaar_id": apaar,
                    "full_name": full_name,
                    "dob": dob.isoformat(),
                    "gender": gender,
                }
            )

    return students, intake_records, registry_records


def inject_defects(
    clean_students: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Inject specific defects at known rows and return (defective_rows, defect_catalog).

    Spread across V002, V005, V006, V007, V008.
    Row numbers are 1-indexed spreadsheet rows (data row idx + 2).
    """
    students_copy = [dict(s) for s in clean_students]
    defects: list[dict[str, Any]] = []

    # 1. Row 10 (idx 8): V002 - apaar_id 11 digits
    row_num = 10
    idx = row_num - 2
    students_copy[idx]["apaar_id"] = "12345678901"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V002",
            "field": "apaar_id",
            "description": "apaar_id has 11 digits",
        }
    )

    # 2. Row 20 (idx 18): V002 - apaar_id with alphabet
    row_num = 20
    idx = row_num - 2
    students_copy[idx]["apaar_id"] = "12345678901A"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V002",
            "field": "apaar_id",
            "description": "apaar_id contains alphanumeric characters",
        }
    )

    # 3. Row 30 (idx 28): V002 - apaar_id with 13 digits
    row_num = 30
    idx = row_num - 2
    students_copy[idx]["apaar_id"] = "9999888877771"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V002",
            "field": "apaar_id",
            "description": "apaar_id has 13 digits",
        }
    )

    # 4. Row 40 (idx 38): V005 - empty full_name
    row_num = 40
    idx = row_num - 2
    students_copy[idx]["full_name"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V005",
            "field": "full_name",
            "description": "Required field full_name is empty",
        }
    )

    # 5. Row 50 (idx 48): V005 - empty dob
    row_num = 50
    idx = row_num - 2
    students_copy[idx]["dob"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V005",
            "field": "dob",
            "description": "Required field dob is empty",
        }
    )

    # 6. Row 60 (idx 58): V005 - empty category
    row_num = 60
    idx = row_num - 2
    students_copy[idx]["category"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V005",
            "field": "category",
            "description": "Required field category is empty",
        }
    )

    # 7. Row 70 (idx 68): V005 - empty admission_date
    row_num = 70
    idx = row_num - 2
    students_copy[idx]["admission_date"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V005",
            "field": "admission_date",
            "description": "Required field admission_date is empty",
        }
    )

    # 8. Row 80 (idx 78): V006 - invalid date format for dob (slash instead of hyphen)
    row_num = 80
    idx = row_num - 2
    students_copy[idx]["dob"] = "15/08/2005"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "dob",
            "description": "Invalid date format for dob: 15/08/2005",
        }
    )

    # 9. Row 90 (idx 88): V006 - invalid date value for admission_date (month 13)
    row_num = 90
    idx = row_num - 2
    students_copy[idx]["admission_date"] = "2026-13-40"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "admission_date",
            "description": "Invalid date format for admission_date: 2026-13-40",
        }
    )

    # 10. Row 100 (idx 98): V006 - invalid gender enum
    row_num = 100
    idx = row_num - 2
    students_copy[idx]["gender"] = "X"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "gender",
            "description": "Invalid enum value 'X' for gender",
        }
    )

    # 11. Row 110 (idx 108): V006 - invalid category enum
    row_num = 110
    idx = row_num - 2
    students_copy[idx]["category"] = "GENERAL"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "category",
            "description": "Invalid enum value 'GENERAL' for category",
        }
    )

    # 12. Row 120 (idx 118): V006 - invalid course_level enum
    row_num = 120
    idx = row_num - 2
    students_copy[idx]["course_level"] = "BACHELORS"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "course_level",
            "description": "Invalid enum value 'BACHELORS' for course_level",
        }
    )

    # 13. Row 130 (idx 128): V006 - invalid nationality (not 2-letter ISO)
    row_num = 130
    idx = row_num - 2
    students_copy[idx]["nationality"] = "INDIA"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "nationality",
            "description": "Invalid nationality 'INDIA' (must be 2-letter ISO code)",
        }
    )

    # 14. Row 140 (idx 138): V006 - invalid email
    row_num = 140
    idx = row_num - 2
    students_copy[idx]["email"] = "not_an_email_at_all"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "email",
            "description": "Invalid email format",
        }
    )

    # 15. Row 150 (idx 148): V006 - invalid mobile
    row_num = 150
    idx = row_num - 2
    students_copy[idx]["mobile"] = "12345"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V006",
            "field": "mobile",
            "description": "Invalid mobile format (too short)",
        }
    )

    # 16. Rows 160 & 165 (idx 158 & 163): V007 - duplicate apaar_id in batch
    dup_apaar = clean_students[158]["apaar_id"]
    students_copy[163]["apaar_id"] = dup_apaar
    students_copy[163]["full_name"] = clean_students[158]["full_name"]
    students_copy[163]["dob"] = clean_students[158]["dob"]
    students_copy[163]["gender"] = clean_students[158]["gender"]
    defects.append(
        {
            "row": 160,
            "rule_id": "V007",
            "field": "apaar_id",
            "description": f"Duplicate apaar_id {dup_apaar} at row 160",
        }
    )
    defects.append(
        {
            "row": 165,
            "rule_id": "V007",
            "field": "apaar_id",
            "description": f"Duplicate apaar_id {dup_apaar} at row 165",
        }
    )

    # 17. Rows 180 & 185 (idx 178 & 183): V008 - duplicate institution_student_id
    students_copy[183]["institution_aicte_id"] = students_copy[178][
        "institution_aicte_id"
    ]
    students_copy[183]["academic_year"] = students_copy[178]["academic_year"]
    dup_roll = students_copy[178]["institution_student_id"]
    students_copy[183]["institution_student_id"] = dup_roll
    defects.append(
        {
            "row": 180,
            "rule_id": "V008",
            "field": "institution_student_id",
            "description": f"Duplicate student ID {dup_roll} at row 180",
        }
    )
    defects.append(
        {
            "row": 185,
            "rule_id": "V008",
            "field": "institution_student_id",
            "description": f"Duplicate student ID {dup_roll} at row 185",
        }
    )

    # 18. Row 200 (idx 198): V014 - OCI with nationality IN
    row_num = 200
    idx = row_num - 2
    students_copy[idx]["quota"] = "OCI"
    students_copy[idx]["nationality"] = "IN"
    students_copy[idx]["oci_status"] = "True"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V014",
            "field": "nationality",
            "description": "OCI student with Indian nationality",
        }
    )

    # 19. Row 210 (idx 208): V014 - FN with nationality IN
    row_num = 210
    idx = row_num - 2
    students_copy[idx]["quota"] = "FN"
    students_copy[idx]["nationality"] = "IN"
    students_copy[idx]["fn_status"] = "True"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V014",
            "field": "nationality",
            "description": "Foreign National student with Indian nationality",
        }
    )

    # 20. Row 220 (idx 218): V014 - NRI quota with nri_status=False
    row_num = 220
    idx = row_num - 2
    students_copy[idx]["quota"] = "NRI"
    students_copy[idx]["nri_status"] = "False"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V014",
            "field": "nri_status",
            "description": "NRI quota with nri_status=False",
        }
    )

    # 21. Row 230 (idx 228): V015 - SUPERNUMERARY seat without scheme
    row_num = 230
    idx = row_num - 2
    students_copy[idx]["seat_type"] = "SUPERNUMERARY"
    students_copy[idx]["supernumerary_scheme"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V015",
            "field": "supernumerary_scheme",
            "description": "SUPERNUMERARY seat without scheme",
        }
    )

    # 22. Row 240 (idx 238): V015 - Scheme assigned to REGULAR seat
    row_num = 240
    idx = row_num - 2
    students_copy[idx]["seat_type"] = "REGULAR"
    students_copy[idx]["supernumerary_scheme"] = "TFW"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V015",
            "field": "supernumerary_scheme",
            "description": "Supernumerary scheme on REGULAR seat",
        }
    )

    # 23. Row 250 (idx 248): V016 - Implausible age for PHD (age 18 < 21)
    row_num = 250
    idx = row_num - 2
    students_copy[idx]["course_level"] = "PHD"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V016",
            "field": "dob",
            "description": "Student age 18 is implausible for course_level 'PHD' (min 21)",
        }
    )

    # 24. Row 260 (idx 258): V017 - Admission date outside academic window
    row_num = 260
    idx = row_num - 2
    students_copy[idx]["admission_date"] = "2025-01-15"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V017",
            "field": "admission_date",
            "description": "admission_date 2025-01-15 outside 2026-27 window",
        }
    )

    # 25. Row 270 (idx 268): V018 - Consent status missing / not GRANTED
    row_num = 270
    idx = row_num - 2
    students_copy[idx]["consent_status"] = "REFUSED"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V018",
            "field": "consent_status",
            "description": "consent_status is REFUSED",
        }
    )

    # 26. Row 280 (idx 278): V018 - Minor without guardian consent (age 17)
    row_num = 280
    idx = row_num - 2
    students_copy[idx]["guardian_consent"] = ""
    defects.append(
        {
            "row": row_num,
            "rule_id": "V018",
            "field": "guardian_consent",
            "description": "Minor student without guardian consent",
        }
    )

    # 27. Row 290 (idx 288): V019 - Program not in approved programs
    row_num = 290
    idx = row_num - 2
    students_copy[idx]["program_code"] = "UG-AEROSPACE"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V019",
            "field": "program_code",
            "description": "Program UG-AEROSPACE is not approved",
        }
    )

    # 28. Row 300 (idx 298): V003 - APAAR ID not in mock registry
    row_num = 300
    idx = row_num - 2
    students_copy[idx]["apaar_id"] = "777711112222"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V003",
            "field": "apaar_id",
            "description": "apaar_id 777711112222 not in mock registry",
        }
    )

    # 29. Row 310 (idx 308): V004 - Uploaded name does not match registry
    row_num = 310
    idx = row_num - 2
    students_copy[idx]["full_name"] = "Totally Mismatched Name"
    defects.append(
        {
            "row": row_num,
            "rule_id": "V004",
            "field": "full_name",
            "description": "Uploaded name does not match APAAR registry name",
        }
    )

    # 30. Over-intake: V012
    # In 1-10002 UG-MECH, approved intake is 65.
    # Base dataset has 63 regular and 4 supernumerary students at rows 400, 401, 402, 403.
    # Converting these 4 supernumerary students to REGULAR increases regular enrolment to 67.
    # Rows 400 and 401 are students 64 and 65 (within approved limit 65).
    # Rows 402 and 403 are students 66 and 67 (exceed approved intake 65 by 2).
    for r in (400, 401, 402, 403):
        students_copy[r - 2]["seat_type"] = "REGULAR"
        students_copy[r - 2]["supernumerary_scheme"] = ""

    defects.append(
        {
            "row": 402,
            "rule_id": "V012",
            "field": "approved_intake",
            "description": "Regular enrolment exceeds approved intake (65) for UG-MECH",
        }
    )
    defects.append(
        {
            "row": 403,
            "rule_id": "V012",
            "field": "approved_intake",
            "description": "Regular enrolment exceeds approved intake (65) for UG-MECH",
        }
    )

    # 31. Rows 320 & 325 (idx 318 & 323): V009 - Krishna / Krushna transliteration variant
    students_copy[318]["full_name"] = "Krishna Joshi"
    students_copy[323]["full_name"] = "Krushna Joshi"
    students_copy[323]["dob"] = students_copy[318]["dob"]
    students_copy[323]["gender"] = students_copy[318]["gender"]
    defects.append(
        {
            "row": 320,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (Krishna/Krushna transliteration variant)",
        }
    )
    defects.append(
        {
            "row": 325,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (Krishna/Krushna transliteration variant)",
        }
    )

    # 32. Rows 340 & 345 (idx 338 & 343): V009 - Bhairoo / Bheru transliteration variant
    students_copy[338]["full_name"] = "Bhairoo Sharma"
    students_copy[343]["full_name"] = "Bheru Sharma"
    students_copy[343]["dob"] = students_copy[338]["dob"]
    students_copy[343]["gender"] = students_copy[338]["gender"]
    defects.append(
        {
            "row": 340,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (Bhairoo/Bheru transliteration variant)",
        }
    )
    defects.append(
        {
            "row": 345,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (Bhairoo/Bheru transliteration variant)",
        }
    )

    # 33. Rows 360 & 365 (idx 358 & 363): V009 - Initials variant (Anil Kumar vs A. K.)
    students_copy[358]["full_name"] = "Anil Kumar Sharma"
    students_copy[363]["full_name"] = "A. K. Sharma"
    students_copy[363]["dob"] = students_copy[358]["dob"]
    students_copy[363]["gender"] = students_copy[358]["gender"]
    defects.append(
        {
            "row": 360,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (initials variant Anil Kumar vs A. K.)",
        }
    )
    defects.append(
        {
            "row": 365,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (initials variant Anil Kumar vs A. K.)",
        }
    )

    # 34. Rows 380 & 385 (idx 378 & 383): V009 - Swapped name order (Aarav Verma vs Verma Aarav)
    students_copy[378]["full_name"] = "Aarav Verma"
    students_copy[383]["full_name"] = "Verma Aarav"
    students_copy[383]["dob"] = students_copy[378]["dob"]
    students_copy[383]["gender"] = students_copy[378]["gender"]
    defects.append(
        {
            "row": 380,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (swapped name order Aarav Verma vs Verma Aarav)",
        }
    )
    defects.append(
        {
            "row": 385,
            "rule_id": "V009",
            "field": "full_name",
            "description": "Probable intra-batch duplicate (swapped name order Aarav Verma vs Verma Aarav)",
        }
    )

    # 35. Row 412 (idx 410): V010 - Same APAAR ACTIVE at another institution
    defects.append(
        {
            "row": 412,
            "rule_id": "V010",
            "field": "apaar_id",
            "description": "Same APAAR ACTIVE at another institution in same academic year",
        }
    )

    # 36. Row 422 (idx 420): V011 - Cross-institution fuzzy duplicate under different APAAR
    students_copy[420]["full_name"] = "Krishna Joshi"
    defects.append(
        {
            "row": 422,
            "rule_id": "V011",
            "field": "full_name",
            "description": "Cross-institution probable same person under different APAAR (Krishna vs Krushna)",
        }
    )

    return students_copy, defects


def generate_dataset(output_dir: Path = OUTPUT_DIR) -> None:
    """Generate all synthetic data artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_students, intake_records, registry_records = generate_clean_dataset()

    # 1. Write intake.csv
    intake_csv_path = output_dir / "intake.csv"
    with open(intake_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "institution_aicte_id",
                "program_code",
                "academic_year",
                "approved_intake",
                "supernumerary_allowed",
                "approval_letter_ref",
            ],
        )
        writer.writeheader()
        writer.writerows(intake_records)

    # 2. Write clean students.csv
    students_csv_path = output_dir / "students.csv"
    student_fieldnames = [
        "apaar_id",
        "institution_aicte_id",
        "institution_student_id",
        "full_name",
        "dob",
        "gender",
        "category",
        "pwd",
        "program_code",
        "course_level",
        "academic_year",
        "admission_date",
        "admission_type",
        "seat_type",
        "supernumerary_scheme",
        "quota",
        "nationality",
        "nri_status",
        "oci_status",
        "fn_status",
        "enrolment_status",
        "consent_status",
        "consent_date",
        "guardian_consent",
        "email",
        "mobile",
    ]
    with open(students_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=student_fieldnames)
        writer.writeheader()
        writer.writerows(clean_students)

    # 3. Write registry.csv exactly matching clean_students
    registry_csv_path = output_dir / "registry.csv"
    with open(registry_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["apaar_id", "full_name", "dob", "gender"]
        )
        writer.writeheader()
        writer.writerows(registry_records)

    # 4. Generate & write defective dataset and defects.json
    defective_students, defects = inject_defects(clean_students)

    defective_csv_path = output_dir / "students_with_defects.csv"
    with open(defective_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=student_fieldnames)
        writer.writeheader()
        writer.writerows(defective_students)

    defects_json_path = output_dir / "defects.json"
    with open(defects_json_path, mode="w", encoding="utf-8") as f:
        json.dump(defects, f, indent=2)

    # 5. Write central_snapshot.csv for cross-institution testing (V010, V011)
    central_records = [
        dict(s) for s in clean_students if s["institution_aicte_id"] != "1-10001"
    ]

    # Seed cross-institution double enrolment for student 410 (Row 412) -> V010
    v010_student = defective_students[410]
    central_records.append(
        {
            **v010_student,
            "institution_aicte_id": "1-10002",
            "enrolment_status": "ACTIVE",
            "academic_year": "2026-27",
        }
    )

    # Seed cross-institution fuzzy duplicate under different APAAR for student 420 (Row 422) -> V011
    v011_student = defective_students[420]
    central_records.append(
        {
            **v011_student,
            "apaar_id": "999911110000",
            "full_name": "Krushna Joshi",
            "institution_aicte_id": "1-10004",
            "enrolment_status": "ACTIVE",
            "academic_year": "2026-27",
        }
    )

    central_csv_path = output_dir / "central_snapshot.csv"
    with open(central_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=student_fieldnames)
        writer.writeheader()
        writer.writerows(central_records)

    # 6. Write history_states.json for metric anomaly testing (V020)
    history_states = [
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2023-24",
            "batch_id": "hist-batch-001",
            "rows_total": 200,
            "null_rate_per_column": {"full_name": 0.0, "dob": 0.0, "gender": 0.0},
            "duplicate_rate": 0.0,
            "nri_share": 0.020,
            "oci_share": 0.0,
            "fn_share": 0.0,
            "supernumerary_share": 0.030,
            "intake_fill_ratio": 0.95,
        },
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2024-25",
            "batch_id": "hist-batch-002",
            "rows_total": 205,
            "null_rate_per_column": {"full_name": 0.0, "dob": 0.0, "gender": 0.0},
            "duplicate_rate": 0.0,
            "nri_share": 0.025,
            "oci_share": 0.0,
            "fn_share": 0.0,
            "supernumerary_share": 0.035,
            "intake_fill_ratio": 0.96,
        },
        {
            "institution_aicte_id": "1-10001",
            "academic_year": "2025-26",
            "batch_id": "hist-batch-003",
            "rows_total": 210,
            "null_rate_per_column": {"full_name": 0.0, "dob": 0.0, "gender": 0.0},
            "duplicate_rate": 0.0,
            "nri_share": 0.022,
            "oci_share": 0.0,
            "fn_share": 0.0,
            "supernumerary_share": 0.028,
            "intake_fill_ratio": 0.94,
        },
    ]
    history_json_path = output_dir / "history_states.json"
    with open(history_json_path, mode="w", encoding="utf-8") as f:
        json.dump(history_states, f, indent=2)

    print(
        f"Generated 1000 clean students, 1000 students with {len(defects)} defects, "
        f"{len(central_records)} central snapshot records, and {len(intake_records)} intake records into {output_dir}"
    )


if __name__ == "__main__":
    generate_dataset()
