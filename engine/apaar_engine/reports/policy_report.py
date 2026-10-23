"""engine/apaar_engine/reports/policy_report.py

Policy and regulatory report aggregations for APAAR-SDMS:
- Generates aggregate tables by state, program, category, quota, and academic year.
- Applies privacy-preserving small-cell suppression (counts < 5 displayed as "<5").
- Exports multi-sheet Excel workbooks (.xlsx) and pandas DataFrames.

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

# Default AICTE institution ID to State mapping
DEFAULT_INSTITUTION_STATE_MAP: Dict[str, str] = {
    "1-10001": "Karnataka",
    "1-10002": "Maharashtra",
    "1-10003": "Delhi",
    "1-10004": "Tamil Nadu",
    "1-10005": "Maharashtra",
}


def apply_small_cell_suppression(
    df: pd.DataFrame,
    threshold: int = 5,
    suppress_label: str = "<5",
    suppress_zero: bool = False,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Apply small-cell suppression to numerical count columns for privacy preservation.

    Counts strictly between 1 and threshold - 1 (1 <= count < 5) are replaced with '<5'.
    If suppress_zero is True, 0 is also replaced with '<5'.
    """
    out_df = df.copy()
    target_cols = columns or [
        c
        for c in out_df.columns
        if pd.api.types.is_numeric_dtype(out_df[c]) and not c.startswith("_")
    ]

    for col in target_cols:
        if col not in out_df.columns:
            continue

        def _suppress_val(v: Any) -> Any:
            try:
                num = float(v)
                if pd.isna(num):
                    return v
                int_num = int(num)
                if suppress_zero and int_num < threshold:
                    return suppress_label
                if not suppress_zero and 1 <= int_num < threshold:
                    return suppress_label
                return int_num
            except (ValueError, TypeError):
                return v

        out_df[col] = out_df[col].apply(_suppress_val)

    return out_df


def _prepare_enriched_dataframe(
    df: pd.DataFrame,
    institution_state_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Ensure clean column formats and derive state from institution ID if needed."""
    edf = df.copy()
    state_map = {**DEFAULT_INSTITUTION_STATE_MAP, **(institution_state_map or {})}

    if "state" not in edf.columns or edf["state"].isna().all():
        if "institution_aicte_id" in edf.columns:
            edf["state"] = (
                edf["institution_aicte_id"]
                .astype(str)
                .str.strip()
                .map(lambda iid: state_map.get(iid, "Other / Central"))
            )
        else:
            edf["state"] = "All States"

    # Normalize categorical columns
    for col in ("program_code", "category", "quota", "seat_type", "gender", "academic_year"):
        if col in edf.columns:
            edf[col] = edf[col].fillna("UNKNOWN").astype(str).str.strip().str.upper()

    return edf


def build_policy_aggregates(
    df: pd.DataFrame,
    institution_state_map: Optional[Dict[str, str]] = None,
    suppress: bool = True,
    threshold: int = 5,
) -> Dict[str, pd.DataFrame]:
    """Generate policy aggregate DataFrames: by state, program, category, quota, and year.

    If suppress is True, applies small-cell suppression (< 5 -> '<5').
    """
    if df.empty:
        empty_df = pd.DataFrame()
        return {
            "by_state": empty_df,
            "by_program": empty_df,
            "by_category": empty_df,
            "by_quota": empty_df,
            "by_year": empty_df,
            "state_x_program": empty_df,
            "category_x_quota": empty_df,
        }

    edf = _prepare_enriched_dataframe(df, institution_state_map)

    # 1. By State
    state_rows = []
    for state, grp in edf.groupby("state"):
        tot = len(grp)
        reg = int((grp["seat_type"] == "REGULAR").sum()) if "seat_type" in grp.columns else tot
        sup = int((grp["seat_type"] == "SUPERNUMERARY").sum()) if "seat_type" in grp.columns else 0
        gen = int((grp["category"] == "GEN").sum()) if "category" in grp.columns else 0
        obc = int((grp["category"] == "OBC-NCL").sum()) if "category" in grp.columns else 0
        sc = int((grp["category"] == "SC").sum()) if "category" in grp.columns else 0
        st = int((grp["category"] == "ST").sum()) if "category" in grp.columns else 0
        ews = int((grp["category"] == "EWS").sum()) if "category" in grp.columns else 0
        nri = int((grp["quota"] == "NRI").sum()) if "quota" in grp.columns else 0
        fn = int(grp["quota"].isin(["FN", "OCI", "PIO"]).sum()) if "quota" in grp.columns else 0

        state_rows.append(
            {
                "State": state,
                "Total Students": tot,
                "Regular": reg,
                "Supernumerary": sup,
                "GEN": gen,
                "OBC-NCL": obc,
                "SC": sc,
                "ST": st,
                "EWS": ews,
                "NRI": nri,
                "OCI/FN": fn,
            }
        )
    df_state = pd.DataFrame(state_rows)

    # 2. By Program
    prog_col = "program_code" if "program_code" in edf.columns else "program"
    prog_rows = []
    if prog_col in edf.columns:
        for prog, grp in edf.groupby(prog_col):
            tot = len(grp)
            reg = int((grp["seat_type"] == "REGULAR").sum()) if "seat_type" in grp.columns else tot
            sup = (
                int((grp["seat_type"] == "SUPERNUMERARY").sum())
                if "seat_type" in grp.columns
                else 0
            )
            gen = int((grp["category"] == "GEN").sum()) if "category" in grp.columns else 0
            obc = int((grp["category"] == "OBC-NCL").sum()) if "category" in grp.columns else 0
            sc = int((grp["category"] == "SC").sum()) if "category" in grp.columns else 0
            st = int((grp["category"] == "ST").sum()) if "category" in grp.columns else 0
            ews = int((grp["category"] == "EWS").sum()) if "category" in grp.columns else 0
            nri = int((grp["quota"] == "NRI").sum()) if "quota" in grp.columns else 0

            prog_rows.append(
                {
                    "Program": prog,
                    "Total Students": tot,
                    "Regular": reg,
                    "Supernumerary": sup,
                    "GEN": gen,
                    "OBC-NCL": obc,
                    "SC": sc,
                    "ST": st,
                    "EWS": ews,
                    "NRI": nri,
                }
            )
    df_prog = pd.DataFrame(prog_rows)

    # 3. By Category
    cat_rows = []
    if "category" in edf.columns:
        for cat, grp in edf.groupby("category"):
            tot = len(grp)
            male = int((grp["gender"] == "M").sum()) if "gender" in grp.columns else 0
            female = int((grp["gender"] == "F").sum()) if "gender" in grp.columns else 0
            other = tot - (male + female)
            reg = int((grp["seat_type"] == "REGULAR").sum()) if "seat_type" in grp.columns else tot
            sup = (
                int((grp["seat_type"] == "SUPERNUMERARY").sum())
                if "seat_type" in grp.columns
                else 0
            )
            cat_rows.append(
                {
                    "Category": cat,
                    "Total Students": tot,
                    "Male": male,
                    "Female": female,
                    "Other": other,
                    "Regular": reg,
                    "Supernumerary": sup,
                }
            )
    df_cat = pd.DataFrame(cat_rows)

    # 4. By Quota
    quota_rows = []
    if "quota" in edf.columns:
        for q, grp in edf.groupby("quota"):
            tot = len(grp)
            reg = int((grp["seat_type"] == "REGULAR").sum()) if "seat_type" in grp.columns else tot
            sup = (
                int((grp["seat_type"] == "SUPERNUMERARY").sum())
                if "seat_type" in grp.columns
                else 0
            )
            quota_rows.append(
                {
                    "Quota": q,
                    "Total Students": tot,
                    "Regular": reg,
                    "Supernumerary": sup,
                }
            )
    df_quota = pd.DataFrame(quota_rows)

    # 5. By Academic Year
    year_rows = []
    yr_col = "academic_year" if "academic_year" in edf.columns else None
    if yr_col:
        for yr, grp in edf.groupby(yr_col):
            tot = len(grp)
            reg = int((grp["seat_type"] == "REGULAR").sum()) if "seat_type" in grp.columns else tot
            sup = (
                int((grp["seat_type"] == "SUPERNUMERARY").sum())
                if "seat_type" in grp.columns
                else 0
            )
            progs = int(grp[prog_col].nunique()) if prog_col in grp.columns else 1
            year_rows.append(
                {
                    "Academic Year": yr,
                    "Total Students": tot,
                    "Regular": reg,
                    "Supernumerary": sup,
                    "Total Programs": progs,
                }
            )
    df_year = pd.DataFrame(year_rows)

    # 6. Cross-Tabulations
    if "state" in edf.columns and prog_col in edf.columns:
        df_state_prog = (
            pd.crosstab(edf["state"], edf[prog_col], margins=True, margins_name="Total")
            .reset_index()
            .rename(columns={"state": "State"})
        )
    else:
        df_state_prog = pd.DataFrame()

    if "category" in edf.columns and "quota" in edf.columns:
        df_cat_quota = (
            pd.crosstab(edf["category"], edf["quota"], margins=True, margins_name="Total")
            .reset_index()
            .rename(columns={"category": "Category"})
        )
    else:
        df_cat_quota = pd.DataFrame()

    aggregates = {
        "by_state": df_state,
        "by_program": df_prog,
        "by_category": df_cat,
        "by_quota": df_quota,
        "by_year": df_year,
        "state_x_program": df_state_prog,
        "category_x_quota": df_cat_quota,
    }

    if suppress:
        suppressed_aggregates = {}
        for name, adf in aggregates.items():
            if not adf.empty:
                suppressed_aggregates[name] = apply_small_cell_suppression(adf, threshold=threshold)
            else:
                suppressed_aggregates[name] = adf
        return suppressed_aggregates

    return aggregates


def _style_excel_sheet(ws: Any, title: str) -> None:
    """Apply AICTE standard navy styling, headers, and borders to worksheet."""
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    num_rows = ws.max_row
    num_cols = ws.max_column

    # Header styling
    for col_idx in range(1, num_cols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align

    # Data styling
    for row_idx in range(2, num_rows + 1):
        for col_idx in range(1, num_cols + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            # First column left-aligned, numbers/labels centered
            if col_idx == 1:
                cell.alignment = left_align
            else:
                cell.alignment = center_align

    # Auto-fit columns
    for col in ws.columns:
        col_letter = col[0].column_letter
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


def export_policy_report_xlsx(
    aggregates_or_df: Union[Dict[str, pd.DataFrame], pd.DataFrame],
    output_path: Optional[Union[str, Path]] = None,
    institution_state_map: Optional[Dict[str, str]] = None,
    suppress: bool = True,
    threshold: int = 5,
) -> bytes:
    """Export policy aggregate tables to a multi-sheet Excel (.xlsx) workbook.

    Sheets:
      1. By State
      2. By Program
      3. By Category
      4. By Quota
      5. By Academic Year
      6. CrossTab State x Program
      7. CrossTab Category x Quota
    """
    if isinstance(aggregates_or_df, pd.DataFrame):
        aggregates = build_policy_aggregates(
            aggregates_or_df,
            institution_state_map=institution_state_map,
            suppress=suppress,
            threshold=threshold,
        )
    else:
        aggregates = aggregates_or_df

    sheet_names = {
        "by_state": "By State",
        "by_program": "By Program",
        "by_category": "By Category",
        "by_quota": "By Quota",
        "by_year": "By Academic Year",
        "state_x_program": "CrossTab State x Program",
        "category_x_quota": "CrossTab Category x Quota",
    }

    wb = openpyxl.Workbook()
    # Remove default active sheet later
    first_sheet = True

    for agg_key, sheet_title in sheet_names.items():
        adf = aggregates.get(agg_key)
        if adf is None or adf.empty:
            continue

        if first_sheet:
            ws = wb.active
            ws.title = sheet_title
            first_sheet = False
        else:
            ws = wb.create_sheet(title=sheet_title)

        # Write header
        ws.append(list(adf.columns))

        # Write rows
        for _, row in adf.iterrows():
            ws.append([None if pd.isna(v) else v for v in row.tolist()])

        _style_excel_sheet(ws, sheet_title)

    buf = io.BytesIO()
    wb.save(buf)
    content = buf.getvalue()

    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    return content
