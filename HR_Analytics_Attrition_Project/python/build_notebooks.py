"""
Generate the four Jupyter notebooks in notebooks/ (nbformat v4 JSON, no Jupyter needed to build them).

Usage
-----
    python python/build_notebooks.py
Notebooks are shipped WITHOUT saved outputs; open them in VS Code / Jupyter and use 'Run All'.
"""
from __future__ import annotations

import json
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[1] / "notebooks"

SETUP = '''import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Image

# Locate the project root whether the notebook is run from notebooks/ or the root
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "python"))

import config as cfg
import data_cleaning as dc
import eda_analysis as eda
import visualization as viz

pd.set_option("display.max_columns", 50)
viz.set_theme()'''


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def notebook(cells: list[dict]) -> dict:
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python", "version": "3.12"}}}


def nb01() -> dict:
    return notebook([
        md("# 01 - Data Exploration\n**HR Analytics & Employee Attrition** | IBM HR Analytics dataset (a fictional dataset created by IBM data scientists)\n\n"
           "Goal: load the raw CSV and understand its structure before cleaning."),
        code(SETUP),
        md("## A. Data collection - load the CSV\n`encoding='utf-8-sig'` removes the byte-order mark (BOM) the file starts with; without it the first column is named `ï»¿Age`."),
        code("raw = dc.load_raw()\nprint('Shape (rows, columns):', raw.shape)"),
        md("### First and last records"),
        code("display(raw.head())\ndisplay(raw.tail())"),
        md("### Data types and memory"),
        code("raw.info()"),
        md("### Summary statistics"),
        code("display(raw.describe().T)"),
        md("### Missing values, duplicates and constant columns"),
        code("""profile = dc.profile(raw)
print('Missing values      :', profile['missing_values_total'])
print('Duplicate rows      :', profile['duplicate_rows'])
print('Duplicate employees :', profile['duplicate_employee_numbers'])
print('Constant columns    :', profile['constant_columns'])"""),
        md("### Cardinality of each column"),
        code("display(raw.nunique().sort_values().to_frame('unique_values'))"),
        md("### Target variable: class balance\nAttrition is imbalanced (far fewer leavers than stayers), so rates matter more than raw counts."),
        code("""counts = raw['Attrition'].value_counts()
display(counts.to_frame('employees').assign(pct=lambda d: (100 * d.employees / d.employees.sum()).round(2)))"""),
        md("### Observations\n- No missing values or duplicate rows.\n- `EmployeeCount`, `Over18`, `StandardHours` are constants and carry no information.\n"
           "- Ordinal survey columns (satisfaction, involvement, ...) are stored as integers 1-4; they are categories, not continuous measures.\n"
           "- Next: `02_Data_Cleaning.ipynb`."),
    ])


def nb02() -> dict:
    return notebook([
        md("# 02 - Data Cleaning\nValidate, correct and enrich the dataset. The same logic lives in `python/data_cleaning.py`."),
        code(SETUP),
        code("raw = dc.load_raw()\nraw.shape"),
        md("## 1. Missing values and duplicates"),
        code("print('Missing:', int(raw.isna().sum().sum()))\nprint('Duplicate rows:', int(raw.duplicated().sum()))\n"
             "print('Duplicate EmployeeNumber:', int(raw['EmployeeNumber'].duplicated().sum()))"),
        md("## 2. Categorical validation\nCompare observed values with the expected domain."),
        code("""for col, domain in cfg.CATEGORICAL_DOMAINS.items():
    unexpected = set(raw[col].unique()) - domain
    print(f"{col:<16} unexpected values: {sorted(unexpected) if unexpected else 'none'}")"""),
        md("## 3. Ordinal range validation"),
        code("""for col, (lo, hi) in cfg.ORDINAL_RANGES.items():
    bad = int(((raw[col] < lo) | (raw[col] > hi)).sum())
    print(f"{col:<26} valid range {lo}-{hi}: out-of-range rows = {bad}")"""),
        md("## 4. Logical consistency\nTenure cannot exceed total working years; the employee must have been old enough to work that long."),
        code("""checks = {
    'YearsAtCompany > TotalWorkingYears': (raw.YearsAtCompany > raw.TotalWorkingYears).sum(),
    'YearsInCurrentRole > YearsAtCompany': (raw.YearsInCurrentRole > raw.YearsAtCompany).sum(),
    'YearsSinceLastPromotion > YearsAtCompany': (raw.YearsSinceLastPromotion > raw.YearsAtCompany).sum(),
    'YearsWithCurrManager > YearsAtCompany': (raw.YearsWithCurrManager > raw.YearsAtCompany).sum(),
}
pd.Series(checks, name='violations')"""),
        md("## 5. Outlier check (IQR rule)\nOutliers are flagged, **not removed**: very high incomes and long tenures are genuine senior employees."),
        code("""cols = ['MonthlyIncome', 'Age', 'YearsAtCompany', 'TotalWorkingYears', 'YearsSinceLastPromotion', 'DistanceFromHome']
display(pd.DataFrame(dc.detect_outliers_iqr(raw, cols)).T)
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
for ax, c in zip(axes.ravel(), cols):
    sns.boxplot(x=raw[c], ax=ax, color=cfg.SKY)
    ax.set_title(c)
plt.tight_layout()
plt.show()"""),
        md("## 6. Run the cleaning pipeline"),
        code("clean, log = dc.clean(raw)\nfor step in log['steps']:\n    print('-', step)\nprint('\\nShape before:', raw.shape, '| after:', clean.shape)"),
        md("## 7. Engineered features"),
        code("display(clean[['Age', 'AgeGroup', 'MonthlyIncome', 'SalarySlab', 'YearsAtCompany', 'TenureBand',\n"
             "               'YearsSinceLastPromotion', 'PromotionGap', 'Attrition', 'AttritionFlag']].head(8))"),
        md("## 8. Save the cleaned dataset"),
        code("cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)\nclean.to_csv(cfg.CLEAN_CSV, index=False)\nprint('Saved ->', cfg.CLEAN_CSV)"),
    ])


def nb03() -> dict:
    return notebook([
        md("# 03 - Exploratory Data Analysis\nAttrition patterns across the workforce. Charts are also saved to `reports/figures/`."),
        code(SETUP),
        code("df = eda.load_clean()\nT = eda.summary_tables(df)\noverall = eda.overall_attrition(df)\ncompany_rate = overall['attrition_rate_pct']\noverall"),
        md("## Overall attrition rate"),
        code("print(f\"Attrition rate: {company_rate}%  ({overall['attrition_count']} of {overall['total_employees']} employees)\")\n"
             "display(Image(viz.fig_attrition_distribution(df)))"),
        md("## Department-wise attrition"),
        code("display(T['by_department'])\ndisplay(Image(viz.fig_department(df, T, company_rate)))"),
        md("## Gender-wise attrition"),
        code("display(T['by_gender'])\ndisplay(Image(viz.fig_gender(df, T, company_rate)))"),
        md("## Age-group attrition and age distribution"),
        code("display(T['by_age_group'])\ndisplay(Image(viz.fig_age_group(df, T, company_rate)))\ndisplay(Image(viz.fig_age_distribution(df)))"),
        md("## Salary-wise attrition"),
        code("display(T['by_salary_slab'])\ndisplay(Image(viz.fig_salary_slab(df, T, company_rate)))\ndisplay(Image(viz.fig_salary_distribution(df)))"),
        md("## Job-role attrition"),
        code("display(T['by_job_role'])\ndisplay(Image(viz.fig_job_role(df, T, company_rate)))"),
        md("## Overtime vs attrition"),
        code("display(T['by_overtime'])\ndisplay(Image(viz.fig_overtime(df, T, company_rate)))"),
        md("## Job satisfaction vs attrition"),
        code("display(T['by_job_satisfaction'])\ndisplay(Image(viz.fig_job_satisfaction(df, T, company_rate)))"),
        md("## Years at company vs attrition (employee experience)"),
        code("display(T['by_tenure_band'])\ndisplay(Image(viz.fig_experience(df)))"),
        md("## Other drivers: business travel, work-life balance, job level, promotion gap"),
        code("for key in ['by_business_travel', 'by_work_life_balance', 'by_job_level', 'by_promotion_gap']:\n    print(key)\n    display(T[key])\n"
             "display(Image(viz.fig_business_travel(df, T, company_rate)))\ndisplay(Image(viz.fig_work_life_balance(df, T, company_rate)))"),
        md("## Correlation heatmap\nPearson correlation between numeric features and `AttritionFlag` (1 = left)."),
        code("display(Image(viz.fig_correlation_heatmap(df)))\ndisplay(eda.numeric_association(df, eda.NUMERIC_FOR_CORR).head(10))"),
        md("## Generate every figure for the report"),
        code("paths = viz.generate_all(df)\nlen(paths)"),
    ])


def nb04() -> dict:
    return notebook([
        md("# 04 - Business Insights\nAnswers to the seven HR questions, computed from the data. **Associations, not causes.**"),
        code(SETUP),
        code("df = eda.load_clean()\nins = eda.compute_insights(df)\nT = ins['tables']\navg = ins['overall']['attrition_rate_pct']\nprint('Company attrition rate:', avg, '%')"),
        md("## Q1. Which department has the highest attrition?"),
        code("d = ins['q1_top_department']\nprint(f\"{d['Department']}: {d['AttritionRatePct']}% ({d['Attrition']} of {d['Employees']})\")\ndisplay(T['by_department'])"),
        md("## Q2. Which job role has the highest turnover?"),
        code("r = ins['q2_top_job_role']\nprint(f\"{r['JobRole']}: {r['AttritionRatePct']}% ({r['Attrition']} of {r['Employees']})\")\ndisplay(T['by_job_role'])"),
        md("## Q3. Does overtime increase attrition?"),
        code("o = ins['q3_overtime']\nprint(f\"Overtime {o['rate_overtime']}% vs no overtime {o['rate_no_overtime']}%  ({o['ratio']}x)\")\nprint('Chi-square test:', o['test'])"),
        md("## Q4. Does lower salary correlate with higher attrition?"),
        code("s = ins['q4_salary']\nprint(s)\ndisplay(T['by_salary_slab'])"),
        md("## Q5. Which age group is most likely to leave?"),
        code("print(ins['q5_age']['top_group'])\ndisplay(T['by_age_group'])"),
        md("## Q6. How does job satisfaction influence attrition?"),
        code("print(ins['q6_job_satisfaction'])\ndisplay(T['by_job_satisfaction'])"),
        md("## Q7. Does promotion frequency affect retention?"),
        code("print('corr(years since promotion, attrition):', round(ins['q7_promotion']['corr_years_since_promotion'], 3))\n"
             "print('Chi-square:', ins['q7_promotion']['test'])\ndisplay(T['by_promotion_gap'])"),
        md("## Strength of association (all drivers)\nCramer's V: ~0.1 small, ~0.3 medium. No single factor is strong, so attrition is multi-factor."),
        code("display(ins['chi_square_all'])"),
        md("## Descriptive risk-factor count (not a predictive model)\nCount of: overtime, job satisfaction <= 2, income < 3,000, tenure <= 2 years."),
        code("""score = ((df.OverTime == 'Yes').astype(int) + (df.JobSatisfaction <= 2).astype(int)
         + (df.MonthlyIncome < 3000).astype(int) + (df.YearsAtCompany <= 2).astype(int))
risk = df.assign(risk_factors=score).groupby('risk_factors').agg(
    employees=('AttritionFlag', 'size'), leavers=('AttritionFlag', 'sum'))
risk['attrition_rate_pct'] = (100 * risk.leavers / risk.employees).round(1)
display(risk)"""),
        md("## Correlation vs causation\nThese are snapshot associations. Leavers differ from stayers on many dimensions at once (age, pay, level, tenure), so no factor is isolated as a *cause*. "
           "Establishing causes requires exit-interview data, longitudinal tracking or controlled policy trials.\n\n"
           "## Recommendations\nSee `reports/Business_Insights_Report.pdf` section *Recommendations for HR management*."),
    ])


def run() -> None:
    NB_DIR.mkdir(exist_ok=True)
    for name, fn in [("01_Data_Exploration", nb01), ("02_Data_Cleaning", nb02),
                     ("03_Exploratory_Data_Analysis", nb03), ("04_Business_Insights", nb04)]:
        path = NB_DIR / f"{name}.ipynb"
        path.write_text(json.dumps(fn(), indent=1), encoding="utf-8")
        print("Wrote", path.name)


if __name__ == "__main__":
    run()
