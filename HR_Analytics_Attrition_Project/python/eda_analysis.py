"""
Exploratory data analysis helpers.

All numbers used in reports are computed here from the data - nothing is typed in by hand.

Usage
-----
    python python/eda_analysis.py        # prints headline results, saves CSV tables
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import config as cfg


def load_clean() -> pd.DataFrame:
    return pd.read_csv(cfg.CLEAN_CSV)


# -------------------------------------------------------------- core metrics
def overall_attrition(df: pd.DataFrame) -> dict:
    total = len(df)
    left = int((df["Attrition"] == "Yes").sum())
    return {
        "total_employees": total,
        "attrition_count": left,
        "active_employees": total - left,
        "attrition_rate_pct": round(100 * left / total, 2),
        "avg_age": round(df["Age"].mean(), 1),
        "avg_monthly_income": round(df["MonthlyIncome"].mean(), 0),
        "avg_years_at_company": round(df["YearsAtCompany"].mean(), 2),
    }


def rate_by(df: pd.DataFrame, col: str, order: list | None = None,
            sort_by_rate: bool = False) -> pd.DataFrame:
    """Headcount / leavers / attrition-rate table for any dimension."""
    g = (df.groupby(col, observed=True)
           .agg(Employees=("EmployeeNumber", "count"),
                Attrition=("AttritionFlag", "sum"),
                AvgMonthlyIncome=("MonthlyIncome", "mean"),
                AvgYearsAtCompany=("YearsAtCompany", "mean"))
           .assign(Active=lambda d: d["Employees"] - d["Attrition"],
                   AttritionRatePct=lambda d: (100 * d["Attrition"] / d["Employees"]).round(2)))
    g[["AvgMonthlyIncome", "AvgYearsAtCompany"]] = g[["AvgMonthlyIncome", "AvgYearsAtCompany"]].round(1)
    if order:
        g = g.reindex(order)
    elif sort_by_rate:
        g = g.sort_values("AttritionRatePct", ascending=False)
    return g.reset_index()


def summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """All dimension tables used across the project."""
    return {
        "by_department": rate_by(df, "Department", sort_by_rate=True),
        "by_gender": rate_by(df, "Gender"),
        "by_age_group": rate_by(df, "AgeGroup", order=cfg.AGE_LABELS),
        "by_salary_slab": rate_by(df, "SalarySlab", order=cfg.SALARY_LABELS),
        "by_job_role": rate_by(df, "JobRole", sort_by_rate=True),
        "by_job_level": rate_by(df, "JobLevel", order=[1, 2, 3, 4, 5]),
        "by_overtime": rate_by(df, "OverTime"),
        "by_business_travel": rate_by(df, "BusinessTravel", sort_by_rate=True),
        "by_marital_status": rate_by(df, "MaritalStatus", sort_by_rate=True),
        "by_job_satisfaction": rate_by(df, "JobSatisfaction", order=[1, 2, 3, 4]),
        "by_environment_satisfaction": rate_by(df, "EnvironmentSatisfaction", order=[1, 2, 3, 4]),
        "by_work_life_balance": rate_by(df, "WorkLifeBalance", order=[1, 2, 3, 4]),
        "by_relationship_satisfaction": rate_by(df, "RelationshipSatisfaction", order=[1, 2, 3, 4]),
        "by_tenure_band": rate_by(df, "TenureBand", order=cfg.TENURE_LABELS),
        "by_promotion_gap": rate_by(df, "PromotionGap", order=cfg.PROMO_LABELS),
        "by_stock_option": rate_by(df, "StockOptionLevel", order=[0, 1, 2, 3]),
    }


def department_profile(df: pd.DataFrame) -> pd.DataFrame:
    return rate_by(df, "Department", sort_by_rate=True)


# ------------------------------------------------------------ statistics
def chi_square(df: pd.DataFrame, col: str) -> dict:
    """Chi-square test of independence between `col` and Attrition."""
    table = pd.crosstab(df[col], df["Attrition"])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    n = table.values.sum()
    cramers_v = float(np.sqrt(chi2 / (n * (min(table.shape) - 1))))
    return {"variable": col, "chi2": round(float(chi2), 2), "dof": int(dof),
            "p_value": float(p), "cramers_v": round(cramers_v, 3)}


def numeric_association(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Point-biserial correlation of numeric columns with AttritionFlag."""
    rows = []
    for c in cols:
        r, p = stats.pointbiserialr(df["AttritionFlag"], df[c])
        rows.append({"variable": c, "correlation_with_attrition": round(float(r), 3),
                     "p_value": float(p)})
    return (pd.DataFrame(rows)
            .sort_values("correlation_with_attrition", key=abs, ascending=False)
            .reset_index(drop=True))


NUMERIC_FOR_CORR = ["Age", "MonthlyIncome", "JobLevel", "TotalWorkingYears", "YearsAtCompany",
                    "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager",
                    "JobSatisfaction", "EnvironmentSatisfaction", "WorkLifeBalance",
                    "RelationshipSatisfaction", "JobInvolvement", "StockOptionLevel",
                    "DistanceFromHome", "NumCompaniesWorked", "PercentSalaryHike",
                    "TrainingTimesLastYear", "PerformanceRating"]


def compute_insights(df: pd.DataFrame) -> dict:
    """Answer the seven business questions with numbers pulled straight from the data."""
    t = summary_tables(df)
    overall = overall_attrition(df)

    dept = t["by_department"]
    role = t["by_job_role"]
    ot = t["by_overtime"].set_index("OverTime")
    sal = t["by_salary_slab"]
    age = t["by_age_group"]
    sat = t["by_job_satisfaction"]
    promo = t["by_promotion_gap"]

    inc_left = df.loc[df.Attrition == "Yes", "MonthlyIncome"]
    inc_stay = df.loc[df.Attrition == "No", "MonthlyIncome"]
    u_stat, u_p = stats.mannwhitneyu(inc_left, inc_stay, alternative="two-sided")

    ot_yes, ot_no = ot.loc["Yes", "AttritionRatePct"], ot.loc["No", "AttritionRatePct"]
    corr = numeric_association(df, NUMERIC_FOR_CORR)

    # attrition among first-3-years employees
    early = df[df["YearsAtCompany"] <= 2]

    return {
        "overall": overall,
        "tables": t,
        "q1_top_department": dept.iloc[0].to_dict(),
        "q2_top_job_role": role.iloc[0].to_dict(),
        "q2_lowest_job_role": role.iloc[-1].to_dict(),
        "q3_overtime": {"rate_overtime": ot_yes, "rate_no_overtime": ot_no,
                        "ratio": round(ot_yes / ot_no, 2), "test": chi_square(df, "OverTime")},
        "q4_salary": {"lowest_slab_rate": float(sal.iloc[0]["AttritionRatePct"]),
                      "highest_slab_rate": float(sal.iloc[-1]["AttritionRatePct"]),
                      "median_income_left": float(inc_left.median()),
                      "median_income_stayed": float(inc_stay.median()),
                      "mannwhitney_p": float(u_p),
                      "corr": float(stats.pointbiserialr(df["AttritionFlag"], df["MonthlyIncome"])[0])},
        "q5_age": {"top_group": age.sort_values("AttritionRatePct", ascending=False).iloc[0].to_dict(),
                   "test": chi_square(df, "AgeGroup")},
        "q6_job_satisfaction": {"rate_low": float(sat.iloc[0]["AttritionRatePct"]),
                                "rate_very_high": float(sat.iloc[-1]["AttritionRatePct"]),
                                "test": chi_square(df, "JobSatisfaction")},
        "q7_promotion": {"table": promo.to_dict("records"),
                         "corr_years_since_promotion": float(
                             corr.loc[corr.variable == "YearsSinceLastPromotion",
                                      "correlation_with_attrition"].iloc[0]),
                         "test": chi_square(df, "PromotionGap")},
        "early_tenure": {"employees": len(early),
                         "rate": round(100 * early["AttritionFlag"].mean(), 2)},
        "correlations": corr,
        "chi_square_all": pd.DataFrame([chi_square(df, c) for c in
                          ["OverTime", "JobRole", "Department", "Gender", "MaritalStatus",
                           "BusinessTravel", "JobSatisfaction", "EnvironmentSatisfaction",
                           "WorkLifeBalance", "StockOptionLevel", "JobLevel", "AgeGroup",
                           "SalarySlab", "TenureBand", "PromotionGap"]])
                          .sort_values("cramers_v", ascending=False).reset_index(drop=True),
    }


def run() -> dict:
    df = load_clean()
    ins = compute_insights(df)
    cfg.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    for name, tbl in ins["tables"].items():
        tbl.to_csv(cfg.TABLES_DIR / f"{name}.csv", index=False)
    ins["correlations"].to_csv(cfg.TABLES_DIR / "numeric_correlations.csv", index=False)
    ins["chi_square_all"].to_csv(cfg.TABLES_DIR / "chi_square_tests.csv", index=False)

    print("OVERALL:", ins["overall"])
    for k in ["q1_top_department", "q2_top_job_role", "q3_overtime", "q4_salary",
              "q5_age", "q6_job_satisfaction", "q7_promotion", "early_tenure"]:
        print(k, "->", ins[k])
    print(ins["chi_square_all"].to_string())
    print(ins["correlations"].head(8).to_string())
    return ins


if __name__ == "__main__":
    run()
