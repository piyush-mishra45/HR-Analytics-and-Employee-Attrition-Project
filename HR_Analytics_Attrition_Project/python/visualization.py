"""
Professional chart generation (Matplotlib + Seaborn).

Usage
-----
    python python/visualization.py      # writes PNGs to reports/figures/
"""
from __future__ import annotations

import sys

import matplotlib
if "ipykernel" not in sys.modules:   # keep inline plotting in notebooks, headless everywhere else
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import config as cfg
import eda_analysis as eda

# ------------------------------------------------------------------ theme
def set_theme() -> None:
    sns.set_theme(style="whitegrid", rc={
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": "#CBD2DE", "grid.color": "#E6EAF1",
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.titlecolor": cfg.NAVY,
        "axes.labelcolor": cfg.NAVY_MID, "xtick.color": "#4A5568", "ytick.color": "#4A5568",
        "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
    })


def _save(fig, name: str) -> str:
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = cfg.FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def _bar_rate(tbl: pd.DataFrame, cat: str, title: str, name: str, horizontal=False,
              avg_rate: float | None = None, xlabel: str | None = None) -> str:
    """Bar chart of attrition rate with n labels and a company-average reference line."""
    fig, ax = plt.subplots(figsize=(9, 5 if not horizontal else max(4, 0.55 * len(tbl) + 1.5)))
    colors = [cfg.RED if r == tbl["AttritionRatePct"].max() else cfg.BLUE
              for r in tbl["AttritionRatePct"]]
    labels = tbl[cat].astype(str)
    if horizontal:
        ax.barh(labels, tbl["AttritionRatePct"], color=colors)
        ax.invert_yaxis()
        for i, (r, n, k) in enumerate(zip(tbl["AttritionRatePct"], tbl["Employees"], tbl["Attrition"])):
            ax.text(r + 0.4, i, f"{r:.1f}%  ({k}/{n})", va="center", fontsize=9, color=cfg.NAVY)
        if avg_rate is not None:
            ax.axvline(avg_rate, color=cfg.GREY, ls="--", lw=1)
            ax.text(avg_rate, -0.7, f"Company avg {avg_rate:.1f}%", color=cfg.GREY, fontsize=8, ha="center")
        ax.set_xlabel("Attrition rate (%)")
        ax.set_xlim(0, tbl["AttritionRatePct"].max() * 1.25)
    else:
        ax.bar(labels, tbl["AttritionRatePct"], color=colors, width=0.62)
        for i, (r, n, k) in enumerate(zip(tbl["AttritionRatePct"], tbl["Employees"], tbl["Attrition"])):
            ax.text(i, r + 0.5, f"{r:.1f}%\n({k}/{n})", ha="center", fontsize=9, color=cfg.NAVY)
        if avg_rate is not None:
            ax.axhline(avg_rate, color=cfg.GREY, ls="--", lw=1)
            ax.text(len(tbl) - 0.5, avg_rate + 0.4, f"Company avg {avg_rate:.1f}%",
                    color=cfg.GREY, fontsize=8, ha="right")
        ax.set_ylabel("Attrition rate (%)")
        ax.set_ylim(0, tbl["AttritionRatePct"].max() * 1.25)
        ax.set_xlabel(xlabel or cat)
    ax.set_title(title, loc="left")
    return _save(fig, name)


# -------------------------------------------------------------------- charts
def fig_attrition_distribution(df):
    counts = df["Attrition"].value_counts().reindex(["No", "Yes"])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=["Active", "Left"], colors=[cfg.BLUE, cfg.RED], startangle=90,
           autopct=lambda p: f"{p:.1f}%\n({int(round(p * counts.sum() / 100))})",
           wedgeprops=dict(width=0.42, edgecolor="white"), textprops=dict(color=cfg.NAVY, fontsize=11))
    ax.set_title("Attrition Distribution", loc="center")
    ax.text(0, 0, f"{len(df):,}\nemployees", ha="center", va="center", fontsize=13,
            color=cfg.NAVY, fontweight="bold")
    return _save(fig, "01_attrition_distribution")


def fig_department(df, tables, avg):
    return _bar_rate(tables["by_department"], "Department", "Attrition Rate by Department",
                     "02_department_attrition", avg_rate=avg)


def fig_age_distribution(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=df, x="Age", hue="Attrition", multiple="stack", bins=22,
                 palette=cfg.PALETTE_STATUS, edgecolor="white", ax=ax)
    ax.set_title("Age Distribution by Attrition Status", loc="left")
    return _save(fig, "03_age_distribution")


def fig_age_group(df, tables, avg):
    return _bar_rate(tables["by_age_group"], "AgeGroup", "Attrition Rate by Age Group",
                     "04_age_group_attrition", avg_rate=avg, xlabel="Age group")


def fig_salary_distribution(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.kdeplot(data=df, x="MonthlyIncome", hue="Attrition", fill=True, common_norm=False,
                palette=cfg.PALETTE_STATUS, alpha=0.35, ax=ax, clip=(0, None))
    for status, ls in [("No", "--"), ("Yes", "--")]:
        med = df.loc[df.Attrition == status, "MonthlyIncome"].median()
        ax.axvline(med, color=cfg.PALETTE_STATUS[status], ls=ls, lw=1)
        ax.text(med, ax.get_ylim()[1] * (0.95 if status == "No" else 0.85),
                f" median ({'active' if status == 'No' else 'left'}): {med:,.0f}",
                color=cfg.PALETTE_STATUS[status], fontsize=9)
    ax.set_title("Monthly Income Distribution by Attrition Status", loc="left")
    ax.set_xlabel("Monthly income (source currency units)")
    return _save(fig, "05_salary_distribution")


def fig_salary_slab(df, tables, avg):
    return _bar_rate(tables["by_salary_slab"], "SalarySlab", "Attrition Rate by Salary Slab",
                     "06_salary_slab_attrition", avg_rate=avg, xlabel="Monthly income slab")


def fig_job_role(df, tables, avg):
    return _bar_rate(tables["by_job_role"], "JobRole", "Attrition Rate by Job Role",
                     "07_job_role_attrition", horizontal=True, avg_rate=avg)


def fig_overtime(df, tables, avg):
    return _bar_rate(tables["by_overtime"], "OverTime", "Attrition Rate: Overtime vs No Overtime",
                     "08_overtime_attrition", avg_rate=avg, xlabel="Works overtime")


def fig_job_satisfaction(df, tables, avg):
    t = tables["by_job_satisfaction"].copy()
    t["JobSatisfaction"] = t["JobSatisfaction"].map(
        lambda v: f"{v} - {cfg.SATISFACTION_LABELS[v]}")
    return _bar_rate(t, "JobSatisfaction", "Attrition Rate by Job Satisfaction",
                     "09_job_satisfaction_attrition", avg_rate=avg, xlabel="Job satisfaction level")


def fig_experience(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.boxplot(data=df, x="Attrition", y="YearsAtCompany", palette=cfg.PALETTE_STATUS,
                hue="Attrition", legend=False, ax=axes[0], order=["No", "Yes"])
    axes[0].set_title("Years at Company", loc="left")
    t = eda.rate_by(df, "TenureBand", order=cfg.TENURE_LABELS)
    colors = [cfg.RED if r == t["AttritionRatePct"].max() else cfg.BLUE for r in t["AttritionRatePct"]]
    axes[1].bar(t["TenureBand"], t["AttritionRatePct"], color=colors, width=0.6)
    for i, r in enumerate(t["AttritionRatePct"]):
        axes[1].text(i, r + 0.5, f"{r:.1f}%", ha="center", fontsize=9, color=cfg.NAVY)
    axes[1].set_title("Attrition Rate by Tenure Band", loc="left")
    axes[1].set_ylabel("Attrition rate (%)")
    axes[1].set_ylim(0, t["AttritionRatePct"].max() * 1.25)
    fig.suptitle("Employee Experience Analysis", x=0.01, ha="left", fontweight="bold", color=cfg.NAVY)
    return _save(fig, "10_experience_analysis")


def fig_correlation_heatmap(df):
    cols = ["AttritionFlag"] + eda.NUMERIC_FOR_CORR
    corr = df[cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(13, 10))
    sns.heatmap(corr, mask=mask, cmap=sns.diverging_palette(10, 250, as_cmap=True), center=0,
                annot=True, fmt=".2f", annot_kws={"size": 7}, linewidths=.4,
                cbar_kws={"shrink": .7}, ax=ax)
    ax.set_title("Correlation Heatmap (numeric features vs AttritionFlag)", loc="left")
    return _save(fig, "11_correlation_heatmap")


def fig_gender(df, tables, avg):
    return _bar_rate(tables["by_gender"], "Gender", "Attrition Rate by Gender",
                     "12_gender_attrition", avg_rate=avg)


def fig_business_travel(df, tables, avg):
    return _bar_rate(tables["by_business_travel"], "BusinessTravel",
                     "Attrition Rate by Business Travel", "13_business_travel_attrition",
                     avg_rate=avg)


def fig_work_life_balance(df, tables, avg):
    t = tables["by_work_life_balance"].copy()
    t["WorkLifeBalance"] = t["WorkLifeBalance"].map(lambda v: f"{v} - {cfg.WLB_LABELS[v]}")
    return _bar_rate(t, "WorkLifeBalance", "Attrition Rate by Work-Life Balance",
                     "14_work_life_balance_attrition", avg_rate=avg)


def fig_promotion_gap(df, tables, avg):
    return _bar_rate(tables["by_promotion_gap"], "PromotionGap",
                     "Attrition Rate by Years Since Last Promotion", "15_promotion_gap_attrition",
                     avg_rate=avg, xlabel="Years since last promotion")


def fig_job_level(df, tables, avg):
    return _bar_rate(tables["by_job_level"], "JobLevel", "Attrition Rate by Job Level",
                     "16_job_level_attrition", avg_rate=avg)


def fig_department_salary(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x="Department", y="MonthlyIncome", hue="Attrition",
                palette=cfg.PALETTE_STATUS, ax=ax)
    ax.set_title("Monthly Income by Department and Attrition", loc="left")
    return _save(fig, "17_department_income")


def generate_all(df: pd.DataFrame | None = None) -> list[str]:
    """Generate every figure; returns the list of file paths."""
    set_theme()
    df = eda.load_clean() if df is None else df
    tables = eda.summary_tables(df)
    avg = eda.overall_attrition(df)["attrition_rate_pct"]
    paths = [
        fig_attrition_distribution(df), fig_department(df, tables, avg),
        fig_age_distribution(df), fig_age_group(df, tables, avg),
        fig_salary_distribution(df), fig_salary_slab(df, tables, avg),
        fig_job_role(df, tables, avg), fig_overtime(df, tables, avg),
        fig_job_satisfaction(df, tables, avg), fig_experience(df),
        fig_correlation_heatmap(df), fig_gender(df, tables, avg),
        fig_business_travel(df, tables, avg), fig_work_life_balance(df, tables, avg),
        fig_promotion_gap(df, tables, avg), fig_job_level(df, tables, avg),
        fig_department_salary(df),
    ]
    print(f"Saved {len(paths)} figures to {cfg.FIGURES_DIR}")
    return paths


if __name__ == "__main__":
    generate_all()
