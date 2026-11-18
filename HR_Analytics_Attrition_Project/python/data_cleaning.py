"""
Data cleaning pipeline for the IBM HR Employee Attrition dataset.

Usage
-----
    python python/data_cleaning.py

Steps (each one is logged into the data-quality report):
  1. Load CSV (handles the UTF-8 BOM present in the original file)
  2. Profile structure, missing values, duplicates
  3. Standardise text, validate categorical domains and ordinal ranges
  4. Correct data types
  5. Flag outliers (IQR rule) - flagged, NOT removed (they are genuine values)
  6. Drop constant columns
  7. Engineer analysis features (age group, salary slab, tenure band ...)
  8. Save cleaned CSV + JSON quality report
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg


# --------------------------------------------------------------------- load
def load_raw(path: Path | str = cfg.RAW_CSV) -> pd.DataFrame:
    """Load the raw CSV. 'utf-8-sig' strips the BOM that the IBM file carries."""
    return pd.read_csv(path, encoding="utf-8-sig")


# ---------------------------------------------------------------- profiling
def profile(df: pd.DataFrame) -> dict:
    """Return basic structure information."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_employee_numbers": int(df["EmployeeNumber"].duplicated().sum()),
        "constant_columns": [c for c in df.columns if df[c].nunique(dropna=False) == 1],
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }


def detect_outliers_iqr(df: pd.DataFrame, columns: list[str], k: float = 1.5) -> dict:
    """Count values outside [Q1 - k*IQR, Q3 + k*IQR] for each numeric column."""
    out = {}
    for col in columns:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        n = int(((df[col] < lo) | (df[col] > hi)).sum())
        out[col] = {"lower_fence": round(float(lo), 2), "upper_fence": round(float(hi), 2),
                    "outlier_count": n, "outlier_pct": round(100 * n / len(df), 2)}
    return out


# ----------------------------------------------------------------- cleaning
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw dataframe. Returns (clean_df, log)."""
    log: dict = {"steps": []}
    df = df.copy()

    # 1. strip whitespace in column names and text values
    df.columns = df.columns.str.strip()
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip()
    log["steps"].append("Stripped whitespace from column names and text values.")

    # 2. missing values: numeric -> median, categorical -> mode (none expected)
    n_missing = int(df.isna().sum().sum())
    for c in df.columns:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].median() if pd.api.types.is_numeric_dtype(df[c])
                                 else df[c].mode()[0])
    log["steps"].append(f"Missing values found: {n_missing} (imputation logic in place).")

    # 3. duplicates
    before = len(df)
    df = df.drop_duplicates().drop_duplicates(subset="EmployeeNumber", keep="first")
    log["steps"].append(f"Duplicate rows removed: {before - len(df)}.")

    # 4. categorical validation
    problems = {}
    for col, domain in cfg.CATEGORICAL_DOMAINS.items():
        bad = set(df[col].unique()) - domain
        if bad:
            problems[col] = sorted(bad)
    log["invalid_categories"] = problems
    log["steps"].append(f"Categorical validation: {len(problems)} column(s) with unexpected values.")

    # 5. ordinal range validation
    range_issues = {}
    for col, (lo, hi) in cfg.ORDINAL_RANGES.items():
        n_bad = int(((df[col] < lo) | (df[col] > hi)).sum())
        if n_bad:
            range_issues[col] = n_bad
    log["out_of_range_ordinals"] = range_issues
    log["steps"].append(f"Ordinal range validation: {len(range_issues)} column(s) with out-of-range values.")

    # 6. logical consistency checks
    inconsistent = {
        "YearsAtCompany > TotalWorkingYears": int((df["YearsAtCompany"] > df["TotalWorkingYears"]).sum()),
        "YearsInCurrentRole > YearsAtCompany": int((df["YearsInCurrentRole"] > df["YearsAtCompany"]).sum()),
        "YearsSinceLastPromotion > YearsAtCompany": int((df["YearsSinceLastPromotion"] > df["YearsAtCompany"]).sum()),
        "YearsWithCurrManager > YearsAtCompany": int((df["YearsWithCurrManager"] > df["YearsAtCompany"]).sum()),
        "Age - TotalWorkingYears < 14": int(((df["Age"] - df["TotalWorkingYears"]) < 14).sum()),
    }
    log["logical_inconsistencies"] = inconsistent
    log["steps"].append("Logical consistency checks run on tenure/age columns.")

    # 7. outliers (flag only)
    num_check = ["MonthlyIncome", "Age", "YearsAtCompany", "TotalWorkingYears",
                 "YearsSinceLastPromotion", "DistanceFromHome", "NumCompaniesWorked"]
    log["outliers_iqr"] = detect_outliers_iqr(df, num_check)
    log["steps"].append("IQR outliers flagged but retained (right-skew in income/tenure is genuine).")

    # 8. dtypes
    int_cols = df.select_dtypes(include="number").columns
    df[int_cols] = df[int_cols].astype("int64")
    for c in ["Attrition", "OverTime", "Gender", "BusinessTravel", "Department",
              "EducationField", "JobRole", "MaritalStatus"]:
        df[c] = df[c].astype("category")
    log["steps"].append("Numeric columns cast to int64; text dimensions cast to category.")

    # 9. drop constant columns
    dropped = [c for c in cfg.CONSTANT_COLUMNS if c in df.columns]
    df = df.drop(columns=dropped)
    log["dropped_constant_columns"] = dropped
    log["steps"].append(f"Dropped constant columns: {dropped}.")

    # 10. feature engineering
    df = add_features(df)
    log["steps"].append("Engineered AttritionFlag, AgeGroup, SalarySlab, TenureBand, PromotionGap (+ sort keys).")

    df = df.sort_values("EmployeeNumber").reset_index(drop=True)
    return df, log


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived analysis columns (also reused by the Streamlit app)."""
    df = df.copy()
    df["AttritionFlag"] = (df["Attrition"].astype(str) == "Yes").astype(int)
    df["AgeGroup"] = pd.cut(df["Age"], cfg.AGE_BINS, labels=cfg.AGE_LABELS).astype(str)
    df["SalarySlab"] = pd.cut(df["MonthlyIncome"], cfg.SALARY_BINS, labels=cfg.SALARY_LABELS).astype(str)
    df["SalarySlabOrder"] = pd.cut(df["MonthlyIncome"], cfg.SALARY_BINS,
                                   labels=range(1, len(cfg.SALARY_LABELS) + 1)).astype(int)
    df["TenureBand"] = pd.cut(df["YearsAtCompany"], cfg.TENURE_BINS, labels=cfg.TENURE_LABELS).astype(str)
    df["TenureBandOrder"] = pd.cut(df["YearsAtCompany"], cfg.TENURE_BINS,
                                   labels=range(1, len(cfg.TENURE_LABELS) + 1)).astype(int)
    df["PromotionGap"] = pd.cut(df["YearsSinceLastPromotion"], cfg.PROMO_BINS,
                                labels=cfg.PROMO_LABELS).astype(str)
    return df


# --------------------------------------------------------------------- main
def run(raw_path: Path = cfg.RAW_CSV, out_path: Path = cfg.CLEAN_CSV) -> pd.DataFrame:
    raw = load_raw(raw_path)
    report = {"raw_profile": profile(raw)}
    clean_df, log = clean(raw)
    report["cleaning_log"] = log
    report["clean_profile"] = {"rows": len(clean_df), "columns": clean_df.shape[1]}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(out_path, index=False)
    cfg.QUALITY_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    cfg.QUALITY_REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))

    print(f"Raw shape   : {raw.shape}")
    print(f"Clean shape : {clean_df.shape}")
    for s in log["steps"]:
        print(" -", s)
    print(f"Saved cleaned data -> {out_path}")
    return clean_df


if __name__ == "__main__":
    run()
