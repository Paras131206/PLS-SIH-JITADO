"""engine/tests/test_parser.py

Tests for CSV and XLSX parser:
- Normalises headers and aliases (e.g., 'APAAR No' -> 'apaar_id')
- Detects encoding (utf-8, utf-8-sig, cp1252)
- Trims cell whitespace
- Preserves 1-indexed row numbers (_row_num)
- Captures corrupted/malformed rows as issues without crashing

Owned by Team A (Data & Intelligence).
"""

import io
from pathlib import Path

import openpyxl

from apaar_engine.parser import detect_encoding, normalize_header_name, parse_file


def test_header_alias_normalization():
    assert normalize_header_name("APAAR No") == "apaar_id"
    assert normalize_header_name("APAAR ID") == "apaar_id"
    assert normalize_header_name("Student ID") == "institution_student_id"
    assert normalize_header_name("Roll Number") == "institution_student_id"
    assert normalize_header_name("Candidate Name") == "full_name"
    assert normalize_header_name("Date of Birth") == "dob"
    assert normalize_header_name("Social Category") == "category"
    assert normalize_header_name("Academic Year") == "academic_year"
    assert normalize_header_name("Email Address") == "email"
    assert normalize_header_name("Mobile No") == "mobile"


def test_detect_encoding():
    utf8_bom = b"\xef\xbb\xbfapaar_id,full_name\n123456789012,Test"
    assert detect_encoding(utf8_bom) == "utf-8-sig"

    plain_utf8 = "apaar_id,full_name\n123456789012,Aarav".encode("utf-8")
    assert detect_encoding(plain_utf8) == "utf-8"

    cp1252_bytes = b"apaar_id,full_name\n123456789012,Ren\xe9e"
    assert detect_encoding(cp1252_bytes) in ("cp1252", "latin-1")


def test_parse_csv_with_whitespace_and_aliases():
    csv_text = (
        " APAAR No , Candidate Name , Date of Birth \n"
        " 123456789012 , Aarav Sharma , 2005-05-10 \n"
        " 987654321098 , Priya Patel  , 2006-06-20 \n"
    )
    stream = io.StringIO(csv_text)
    df, issues = parse_file(stream)

    assert issues == []
    assert list(df.columns) == ["apaar_id", "full_name", "dob", "_row_num"]
    assert len(df) == 2
    assert df["apaar_id"].iloc[0] == "123456789012"
    assert df["full_name"].iloc[0] == "Aarav Sharma"
    assert df["_row_num"].iloc[0] == 2
    assert df["_row_num"].iloc[1] == 3


def test_parse_csv_corrupted_row_does_not_crash():
    # Row 3 has 5 values instead of 3
    csv_text = """apaar_id,full_name,dob
123456789012,Aarav Sharma,2005-05-10
987654321098,Extra,Field,Here,2006-06-20
111122223333,Sneha Rao,2007-07-30
"""
    stream = io.StringIO(csv_text)
    df, issues = parse_file(stream)

    assert len(df) == 3
    assert len(issues) == 1
    assert issues[0].row == 3
    assert issues[0].rule_id == "V006"
    assert "Row has 5 fields, expected 3" in issues[0].message


def test_parse_xlsx_roundtrip(tmp_path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["APAAR ID", "Candidate Name", "DOB"])
    ws.append([" 123456789012 ", " Rohan Gupta ", "2005-08-12"])
    ws.append([" 987654321098 ", " Ananya Iyer ", "2006-09-15"])

    xlsx_path = tmp_path / "test_students.xlsx"
    wb.save(xlsx_path)

    df, issues = parse_file(xlsx_path)
    assert issues == []
    assert len(df) == 2
    assert list(df.columns) == ["apaar_id", "full_name", "dob", "_row_num"]
    assert df["apaar_id"].iloc[0] == "123456789012"
    assert df["full_name"].iloc[0] == "Rohan Gupta"
    assert df["_row_num"].iloc[0] == 2
    assert df["_row_num"].iloc[1] == 3


def test_parse_empty_file():
    empty_stream = io.StringIO("")
    df, issues = parse_file(empty_stream)
    assert df.empty
    assert len(issues) == 1
    assert issues[0].rule_id == "V001"
