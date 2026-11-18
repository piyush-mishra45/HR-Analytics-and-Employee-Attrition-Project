"""
Pure-pandas helpers used by dashboard/app.py (kept free of Streamlit so they can be unit-tested).
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

import data_cleaning as dc
import eda_analysis as eda

REQUIRED_COLUMNS = [
    "Age", "Attrition", "BusinessTravel", "Department", "DistanceFromHome", "Education",
    "EducationField", "EmployeeNumber", "EnvironmentSatisfaction", "Gender", "JobInvolvement",
    "JobLevel", "JobRole", "JobSatisfaction", "MaritalStatus", "MonthlyIncome", "NumCompaniesWorked",
    "OverTime", "PercentSalaryHike", "PerformanceRating", "RelationshipSatisfaction",
    "StockOptionLevel", "TotalWorkingYears", "TrainingTimesLastYear", "WorkLifeBalance",
    "YearsAtCompany", "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager",
]


def read_upload(file_like) -> pd.DataFrame:
    """Read an uploaded CSV (handles BOM) - also accepts a path."""
    return pd.read_csv(file_like, encoding="utf-8-sig")


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accept either the raw IBM CSV or the already-cleaned CSV and return an analysis-ready frame.
    Raises ValueError with a readable message if required columns are missing.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Uploaded file is missing required columns: {', '.join(missing)}")
    if {"AttritionFlag", "AgeGroup", "SalarySlab", "TenureBand", "PromotionGap"} <= set(df.columns):
        out = df.copy()
    else:
        out, _ = dc.clean(df)
    for c in out.select_dtypes("category").columns:
        out[c] = out[c].astype(str)
    return out


def filter_frame(df: pd.DataFrame, departments=None, roles=None, overtime=None) -> pd.DataFrame:
    """Apply sidebar filters; None / empty means 'no filter'."""
    out = df
    if departments:
        out = out[out["Department"].isin(departments)]
    if roles:
        out = out[out["JobRole"].isin(roles)]
    if overtime and overtime != "All":
        out = out[out["OverTime"] == overtime]
    return out


def kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total": 0, "active": 0, "left": 0, "rate": 0.0, "avg_age": 0.0, "avg_income": 0.0}
    o = eda.overall_attrition(df)
    return {"total": o["total_employees"], "active": o["active_employees"], "left": o["attrition_count"],
            "rate": o["attrition_rate_pct"], "avg_age": float(df["Age"].mean()),
            "avg_income": float(df["MonthlyIncome"].mean())}


def results_zip(df: pd.DataFrame) -> bytes:
    """ZIP of every summary table (CSV) for the filtered data."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, tbl in eda.summary_tables(df).items():
            z.writestr(f"{name}.csv", tbl.to_csv(index=False))
    return buf.getvalue()


def results_workbook(df: pd.DataFrame) -> bytes:
    """One Excel workbook with a sheet per summary table."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, tbl in eda.summary_tables(df).items():
            tbl.to_excel(xw, sheet_name=name[3:34], index=False)
    return buf.getvalue()
