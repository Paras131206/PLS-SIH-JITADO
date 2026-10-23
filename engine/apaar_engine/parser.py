"""engine/apaar_engine/parser.py

Robust CSV and XLSX parser for APAAR-SDMS batches.
- Handles CSV & Excel (openpyxl)
- Detects encoding (utf-8, utf-8-sig, latin-1, cp1252)
- Normalises headers (case, whitespace, common aliases)
- Trims whitespace from cells
- Preserves 1-indexed original spreadsheet row numbers (_row_num)
- Captures corrupted/malformed rows as issues without crashing

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

import openpyxl
import pandas as pd

from apaar_engine.models import Issue, Severity

# Canonical header alias dictionary (lowercased without spaces/punctuation)
HEADER_ALIASES: Dict[str, str] = {
    # apaar_id
    "apaar_id": "apaar_id",
    "apaarid": "apaar_id",
    "apaar_no": "apaar_id",
    "apaarno": "apaar_id",
    "apaar_number": "apaar_id",
    "apaarnumber": "apaar_id",
    "apaar": "apaar_id",
    # institution_aicte_id
    "institution_aicte_id": "institution_aicte_id",
    "institutionaicteid": "institution_aicte_id",
    "aicte_id": "institution_aicte_id",
    "aicteid": "institution_aicte_id",
    "institute_aicte_id": "institution_aicte_id",
    "institution_id": "institution_aicte_id",
    # institution_student_id
    "institution_student_id": "institution_student_id",
    "institutionstudentid": "institution_student_id",
    "student_id": "institution_student_id",
    "studentid": "institution_student_id",
    "roll_no": "institution_student_id",
    "rollno": "institution_student_id",
    "roll_number": "institution_student_id",
    "rollnumber": "institution_student_id",
    "enrollment_no": "institution_student_id",
    "enrolment_no": "institution_student_id",
    # full_name
    "full_name": "full_name",
    "fullname": "full_name",
    "student_name": "full_name",
    "studentname": "full_name",
    "name": "full_name",
    "candidate_name": "full_name",
    # dob
    "dob": "dob",
    "date_of_birth": "dob",
    "dateofbirth": "dob",
    "birth_date": "dob",
    "birthdate": "dob",
    # gender
    "gender": "gender",
    "sex": "gender",
    # category
    "category": "category",
    "caste": "category",
    "social_category": "category",
    # pwd
    "pwd": "pwd",
    "physically_challenged": "pwd",
    "handicapped": "pwd",
    "disability": "pwd",
    # program_code
    "program_code": "program_code",
    "programcode": "program_code",
    "program": "program_code",
    "course_code": "program_code",
    "course": "program_code",
    "branch": "program_code",
    "branch_code": "program_code",
    # course_level
    "course_level": "course_level",
    "courselevel": "course_level",
    "degree": "course_level",
    "level": "course_level",
    # academic_year
    "academic_year": "academic_year",
    "academicyear": "academic_year",
    "session": "academic_year",
    "batch": "academic_year",
    "year": "academic_year",
    # admission_date
    "admission_date": "admission_date",
    "admissiondate": "admission_date",
    "date_of_admission": "admission_date",
    "joining_date": "admission_date",
    # admission_type
    "admission_type": "admission_type",
    "admissiontype": "admission_type",
    "type_of_admission": "admission_type",
    # seat_type
    "seat_type": "seat_type",
    "seattype": "seat_type",
    "type_of_seat": "seat_type",
    # supernumerary_scheme
    "supernumerary_scheme": "supernumerary_scheme",
    "supernumeraryscheme": "supernumerary_scheme",
    "scheme": "supernumerary_scheme",
    # quota
    "quota": "quota",
    # nationality
    "nationality": "nationality",
    "country": "nationality",
    "country_of_origin": "nationality",
    # nri_status
    "nri_status": "nri_status",
    "nristatus": "nri_status",
    "is_nri": "nri_status",
    "nri": "nri_status",
    # oci_status
    "oci_status": "oci_status",
    "ocistatus": "oci_status",
    "is_oci": "oci_status",
    "oci": "oci_status",
    # fn_status
    "fn_status": "fn_status",
    "fnstatus": "fn_status",
    "is_fn": "fn_status",
    "fn": "fn_status",
    "foreign_national": "fn_status",
    # enrolment_status
    "enrolment_status": "enrolment_status",
    "enrolmentstatus": "enrolment_status",
    "enrollment_status": "enrolment_status",
    "enrollmentstatus": "enrolment_status",
    "status": "enrolment_status",
    # consent_status
    "consent_status": "consent_status",
    "consentstatus": "consent_status",
    "consent": "consent_status",
    # consent_date
    "consent_date": "consent_date",
    "consentdate": "consent_date",
    # guardian_consent
    "guardian_consent": "guardian_consent",
    "guardianconsent": "guardian_consent",
    "parental_consent": "guardian_consent",
    # email
    "email": "email",
    "email_id": "email",
    "email_address": "email",
    # mobile
    "mobile": "mobile",
    "mobile_no": "mobile",
    "mobile_number": "mobile",
    "phone": "mobile",
    "contact": "mobile",
}


def normalize_header_name(header: Any) -> str:
    """Normalize a raw header string into canonical snake_case using alias mapping."""
    if header is None:
        return ""
    text = str(header).strip()
    # Replace whitespace and hyphens with underscore
    clean = re.sub(r"[\s\-]+", "_", text).lower()
    # Strip any special characters except letters, digits, and underscores
    clean = re.sub(r"[^\w_]", "", clean)
    clean_no_underscore = clean.replace("_", "")

    # 1. Direct alias match
    if clean in HEADER_ALIASES:
        return HEADER_ALIASES[clean]
    if clean_no_underscore in HEADER_ALIASES:
        return HEADER_ALIASES[clean_no_underscore]

    # Return standard clean snake_case
    return clean


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect file encoding from byte content (utf-8-sig, utf-8, latin-1, cp1252)."""
    # Check for UTF-8 Byte Order Mark
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
        return "utf-16"

    # Attempt utf-8 decoding
    try:
        raw_bytes[:65536].decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # Attempt Windows-1252 / latin-1
    try:
        raw_bytes[:65536].decode("cp1252")
        return "cp1252"
    except UnicodeDecodeError:
        return "latin-1"


def parse_csv_stream(
    stream: io.TextIOBase,
    issues: List[Issue],
) -> pd.DataFrame:
    """Parse CSV text stream line by line with robust error recovery for corrupted rows."""
    reader = csv.reader(stream)
    header_raw = None
    file_row_num = 0

    # Read header
    for line in reader:
        file_row_num += 1
        if any(cell.strip() for cell in line):
            header_raw = line
            break

    if not header_raw:
        issues.append(
            Issue(
                row=1,
                field="file_header",
                rule_id="V001",
                severity=Severity.ERROR,
                message="File is empty or contains no non-empty header line",
            )
        )
        return pd.DataFrame()

    normalized_cols = [normalize_header_name(col) for col in header_raw]
    num_cols = len(normalized_cols)

    records: List[Dict[str, Any]] = []

    for line in reader:
        file_row_num += 1
        # Skip completely blank lines
        if not any(cell.strip() for cell in line):
            continue

        if len(line) != num_cols:
            issues.append(
                Issue(
                    row=file_row_num,
                    field="format",
                    rule_id="V006",
                    severity=Severity.ERROR,
                    message=f"Row has {len(line)} fields, expected {num_cols}",
                )
            )
            # If line is longer or shorter, pad or slice to avoid breaking dataframe
            if len(line) < num_cols:
                line = line + [""] * (num_cols - len(line))
            else:
                line = line[:num_cols]

        row_dict = {
            col: str(cell).strip() if cell is not None else ""
            for col, cell in zip(normalized_cols, line)
        }
        row_dict["_row_num"] = file_row_num
        records.append(row_dict)

    if not records:
        df = pd.DataFrame(columns=normalized_cols + ["_row_num"])
    else:
        df = pd.DataFrame(records)

    return df


def parse_xlsx_stream(
    stream: Union[BinaryIO, bytes],
    issues: List[Issue],
) -> pd.DataFrame:
    """Parse XLSX workbook stream with openpyxl, preserving row numbers and trimming cells."""
    try:
        if isinstance(stream, bytes):
            stream = io.BytesIO(stream)
        wb = openpyxl.load_workbook(stream, read_only=True, data_only=True)
        sheet = wb.active
        if sheet is None:
            issues.append(
                Issue(
                    row=1,
                    field="file_header",
                    rule_id="V001",
                    severity=Severity.ERROR,
                    message="Excel workbook has no active sheet",
                )
            )
            return pd.DataFrame()

        rows_iter = sheet.iter_rows(values_only=True)
        header_raw = None
        file_row_num = 0

        for row in rows_iter:
            file_row_num += 1
            if any(cell is not None and str(cell).strip() for cell in row):
                header_raw = row
                break

        if not header_raw:
            issues.append(
                Issue(
                    row=1,
                    field="file_header",
                    rule_id="V001",
                    severity=Severity.ERROR,
                    message="Excel file has no non-empty header row",
                )
            )
            return pd.DataFrame()

        normalized_cols = [normalize_header_name(c) for c in header_raw]
        num_cols = len(normalized_cols)
        records: List[Dict[str, Any]] = []

        for row in rows_iter:
            file_row_num += 1
            if not any(cell is not None and str(cell).strip() for cell in row):
                continue

            row_list = list(row)
            if len(row_list) < num_cols:
                row_list = row_list + [None] * (num_cols - len(row_list))
            elif len(row_list) > num_cols:
                row_list = row_list[:num_cols]

            row_dict: Dict[str, Any] = {}
            for col, cell in zip(normalized_cols, row_list):
                if cell is None:
                    row_dict[col] = ""
                elif isinstance(cell, str):
                    row_dict[col] = cell.strip()
                else:
                    # Convert dates or numbers cleanly
                    row_dict[col] = str(cell).strip()

            row_dict["_row_num"] = file_row_num
            records.append(row_dict)

        if not records:
            df = pd.DataFrame(columns=normalized_cols + ["_row_num"])
        else:
            df = pd.DataFrame(records)

        return df

    except Exception as exc:
        issues.append(
            Issue(
                row=1,
                field="file_format",
                rule_id="V006",
                severity=Severity.ERROR,
                message=f"Failed to read Excel workbook: {exc}",
            )
        )
        return pd.DataFrame()


def parse_file(
    file_or_path: Union[str, Path, bytes, BinaryIO, io.TextIOBase],
    is_excel: Optional[bool] = None,
) -> Tuple[pd.DataFrame, List[Issue]]:
    """Parse CSV or Excel file safely into a pandas DataFrame.

    - Returns (DataFrame, list_of_parsing_issues).
    - Preserves 1-indexed row number in column '_row_num'.
    - Never raises an unhandled parsing exception.
    """
    issues: List[Issue] = []

    # Case 1: Path or filename string
    if isinstance(file_or_path, (str, Path)):
        path = Path(file_or_path)
        if not path.exists():
            issues.append(
                Issue(
                    row=0,
                    field="file_path",
                    rule_id="V006",
                    severity=Severity.ERROR,
                    message=f"File does not exist: {path}",
                )
            )
            return pd.DataFrame(), issues

        ext = path.suffix.lower()
        if is_excel is True or ext in (".xlsx", ".xls"):
            with open(path, "rb") as f:
                df = parse_xlsx_stream(f, issues)
                return df, issues
        else:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            encoding = detect_encoding(raw_bytes)
            text_stream = io.StringIO(raw_bytes.decode(encoding, errors="replace"))
            df = parse_csv_stream(text_stream, issues)
            return df, issues

    # Case 2: In-memory raw bytes
    if isinstance(file_or_path, bytes):
        if is_excel is True or file_or_path.startswith(b"PK\x03\x04"):  # ZIP/XLSX header
            df = parse_xlsx_stream(file_or_path, issues)
            return df, issues
        encoding = detect_encoding(file_or_path)
        text_stream = io.StringIO(file_or_path.decode(encoding, errors="replace"))
        df = parse_csv_stream(text_stream, issues)
        return df, issues

    # Case 3: Binary stream
    if isinstance(file_or_path, (io.RawIOBase, io.BufferedIOBase, BinaryIO)):
        raw_bytes = file_or_path.read()
        return parse_file(raw_bytes, is_excel=is_excel)

    # Case 4: Text stream
    if isinstance(file_or_path, io.TextIOBase):
        df = parse_csv_stream(file_or_path, issues)
        return df, issues

    # Fallback
    issues.append(
        Issue(
            row=0,
            field="file_type",
            rule_id="V006",
            severity=Severity.ERROR,
            message=f"Unsupported file input type: {type(file_or_path)}",
        )
    )
    return pd.DataFrame(), issues
