"""Loading, date detection, sorting and saving. No GUI code in here."""
from __future__ import annotations

import csv
import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

EXCEL_EXTS = {".xlsx", ".xlsm", ".xls"}
CSV_EXTS = {".csv", ".tsv", ".txt"}


@dataclass
class SortRule:
    column: object
    ascending: bool = True
    as_date: bool = False
    dayfirst: bool = True


# --------------------------------------------------------------------------- loading
def is_excel(path: str) -> bool:
    return Path(path).suffix.lower() in EXCEL_EXTS


def excel_sheet_names(path: str) -> list[str]:
    with pd.ExcelFile(path) as xl:
        return list(xl.sheet_names)


def load_excel(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, keep_default_na=False, na_values=[""])
    return df.reset_index(drop=True)


def load_csv(path: str) -> tuple[pd.DataFrame, str]:
    """Read everything as text so values (e.g. 007) are never altered."""
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding, newline="") as f:
                sample = f.read(16384)
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
            df = pd.read_csv(
                path, sep=delimiter, dtype=str, encoding=encoding,
                keep_default_na=False, na_values=[""],
            )
            return df.reset_index(drop=True), delimiter
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error  # type: ignore[misc]


# ----------------------------------------------------------------------- date logic
_DATE_RE = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})")


def detect_dayfirst(series: pd.Series) -> bool:
    """25/12/2024 -> day first. 12/25/2024 -> month first. Ambiguous -> day first."""
    first_gt12 = second_gt12 = False
    for value in series.dropna().astype(str).head(500):
        m = _DATE_RE.match(value)
        if m:
            first_gt12 |= int(m.group(1)) > 12
            second_gt12 |= int(m.group(2)) > 12
    return not (second_gt12 and not first_gt12)


def to_datetime(series: pd.Series, dayfirst: bool) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(series, errors="coerce", dayfirst=dayfirst, format="mixed")


def looks_like_date(series: pd.Series) -> bool:
    if is_datetime64_any_dtype(series):
        return True
    if is_numeric_dtype(series) or is_bool_dtype(series):
        return False
    text = series.dropna().astype(str).str.strip()
    text = text[text != ""].head(200)
    if text.empty:
        return False
    if pd.to_numeric(text, errors="coerce").notna().all():
        return False  # plain numbers such as 2024 or 10 are not dates
    parsed = to_datetime(text, detect_dayfirst(text))
    return bool(parsed.notna().mean() >= 0.8)


# --------------------------------------------------------------------------- sorting
def _build_key(series: pd.Series, rule: SortRule) -> pd.Series:
    if rule.as_date:
        return to_datetime(series, rule.dayfirst)
    if is_datetime64_any_dtype(series):
        return series
    if is_numeric_dtype(series) or is_bool_dtype(series):
        return series

    stripped = series.astype(str).str.strip()
    is_null = series.isna() | (stripped == "")
    nums = pd.to_numeric(stripped.where(~is_null), errors="coerce")
    if (~is_null).any() and nums[~is_null].notna().all():
        return nums  # numbers stored as text sort numerically
    return stripped.str.casefold().where(~is_null)  # case-insensitive text


def sort_dataframe(df: pd.DataFrame, rules: list[SortRule]) -> pd.DataFrame:
    """Multi-column sort. Rule order = priority. Empty cells always go last.
    Column order and the original cell values are left untouched."""
    if not rules:
        raise ValueError("Add at least one sort rule.")
    keys = pd.DataFrame(
        {f"k{i}": _build_key(df[r.column], r).to_numpy() for i, r in enumerate(rules)},
        index=df.index,
    )
    order = keys.sort_values(
        by=list(keys.columns),
        ascending=[r.ascending for r in rules],
        na_position="last",
        kind="stable",
    )
    return df.loc[order.index].reset_index(drop=True)


# ------------------------------------------------------------------ display / saving
def format_cell(value) -> str:
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, datetime):
        if (value.hour, value.minute, value.second, value.microsecond) == (0, 0, 0, 0):
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def save_dataframe(df: pd.DataFrame, path: str, delimiter: str = ",", sheet_name: str = "Sorted") -> None:
    ext = Path(path).suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        _save_excel(df, path, sheet_name)
    else:
        df.to_csv(path, index=False, sep=delimiter, encoding="utf-8-sig")


def _save_excel(df: pd.DataFrame, path: str, sheet_name: str) -> None:
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    sheet_name = re.sub(r"[\[\]:*?/\\]", "_", sheet_name)[:31] or "Sorted"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]
        ws.freeze_panes = "A2"
        for i, col in enumerate(df.columns, start=1):
            letter = get_column_letter(i)
            ws[f"{letter}1"].font = Font(bold=True)
            sample = [len(format_cell(v)) for v in df[col].head(500)]
            ws.column_dimensions[letter].width = min(max([len(str(col))] + sample) + 2, 60)
            series = df[col]
            if is_datetime64_any_dtype(series):
                valid = series.dropna()
                if (valid == valid.dt.normalize()).all():  # no time part -> date only
                    for cell in ws[letter][1:]:
                        cell.number_format = "yyyy-mm-dd"
