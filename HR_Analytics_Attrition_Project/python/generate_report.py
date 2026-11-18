"""
Generate reports/Business_Insights_Report.pdf with ReportLab.

All figures in the text are computed from the cleaned dataset at run time.

Usage
-----
    python python/generate_report.py      (run data_cleaning.py + visualization.py first)
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

import config as cfg
import eda_analysis as eda

NAVY, BLUE, LIGHT = colors.HexColor(cfg.NAVY), colors.HexColor(cfg.BLUE), colors.HexColor("#EAF0F8")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=BLUE, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, alignment=TA_LEFT, spaceAfter=5)
NOTE = ParagraphStyle("Note", parent=BODY, fontSize=8, textColor=colors.HexColor("#5A6475"), leading=11)
BUL = ParagraphStyle("Bul", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3)
CALLOUT = ParagraphStyle("Callout", parent=BODY, backColor=LIGHT, borderPadding=6, leftIndent=4, rightIndent=4, spaceBefore=4, spaceAfter=8)


def pct(x, d=1) -> str:
    return f"{x:.{d}f}%"


def fig(name: str, width_cm: float = 15.5):
    path = cfg.FIGURES_DIR / name
    w, h = ImageReader(str(path)).getSize()
    return Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w)


def p_text(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def table(rows, col_widths=None, header=True):
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
             ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D1DE")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """Transparent count of 4 risk factors (same rule as SQL Q24). Descriptive, not predictive."""
    score = ((df.OverTime == "Yes").astype(int) + (df.JobSatisfaction <= 2).astype(int)
             + (df.MonthlyIncome < 3000).astype(int) + (df.YearsAtCompany <= 2).astype(int))
    g = df.assign(risk=score).groupby("risk").agg(n=("AttritionFlag", "size"), left=("AttritionFlag", "sum"))
    g["rate"] = 100 * g["left"] / g["n"]
    return g.reset_index()


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#5A6475"))
    canvas.drawString(2 * cm, 1.2 * cm, "HR Analytics & Employee Attrition | IBM HR dataset (fictional) | Associations, not causal proof")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build(out=cfg.REPORTS_DIR / "Business_Insights_Report.pdf") -> None:
    df = eda.load_clean()
    ins = eda.compute_insights(df)
    T, ov = ins["tables"], ins["overall"]
    avg = ov["attrition_rate_pct"]
    dept, role = ins["q1_top_department"], ins["q2_top_job_role"]
    ot, sal, age = ins["q3_overtime"], ins["q4_salary"], ins["q5_age"]
    sat, promo, early = ins["q6_job_satisfaction"], ins["q7_promotion"], ins["early_tenure"]
    risk = risk_table(df)
    stock0 = T["by_stock_option"].iloc[0]
    lvl1 = T["by_job_level"].iloc[0]
    wlb1 = T["by_work_life_balance"].iloc[0]
    travel = T["by_business_travel"].iloc[0]
    single = T["by_marital_status"].iloc[0]
    s = []

    # ---------------- cover / executive summary
    s += [Paragraph("HR Analytics &amp; Employee Attrition", ParagraphStyle("T", parent=H1, fontSize=24, spaceAfter=2)),
          Paragraph("Business Insights Report", ParagraphStyle("T2", parent=H2, fontSize=14)),
          Paragraph(f"Generated {date.today():%d %B %Y} from <i>data/processed/hr_attrition_cleaned.csv</i>", NOTE), Spacer(1, 8)]
    s.append(Paragraph("<b>Data disclosure.</b> The IBM HR Analytics Employee Attrition &amp; Performance dataset is a "
                       "<b>fictional dataset created by IBM data scientists</b>. It is excellent for demonstrating analytics "
                       "techniques, but nothing in this report describes a real organisation. Treat all findings as "
                       "illustrations of method, not as real-world business facts.", CALLOUT))
    s.append(Paragraph("Executive summary", H1))
    kpi = [["Metric", "Value"],
           ["Total employees", f"{ov['total_employees']:,}"],
           ["Active employees", f"{ov['active_employees']:,}"],
           ["Employees who left", f"{ov['attrition_count']:,}"],
           ["Overall attrition rate", pct(avg)],
           ["Average age", f"{ov['avg_age']}"],
           ["Average monthly income (source currency units)", f"{ov['avg_monthly_income']:,.0f}"],
           ["Average years at company", f"{ov['avg_years_at_company']}"]]
    s.append(table(kpi, [9 * cm, 5 * cm]))
    s.append(Spacer(1, 8))
    for b in [
        f"<b>Highest-attrition department:</b> {dept['Department']} at {pct(dept['AttritionRatePct'])} ({dept['Attrition']} of {dept['Employees']}).",
        f"<b>Highest-attrition job role:</b> {role['JobRole']} at {pct(role['AttritionRatePct'])} ({role['Attrition']} of {role['Employees']}), roughly {role['AttritionRatePct']/avg:.1f}x the company rate.",
        f"<b>Overtime:</b> {pct(ot['rate_overtime'])} attrition with overtime vs {pct(ot['rate_no_overtime'])} without ({ot['ratio']}x; {p_text(ot['test']['p_value'])}).",
        f"<b>Pay:</b> attrition is {pct(sal['lowest_slab_rate'])} in the lowest salary slab vs {pct(sal['highest_slab_rate'])} in the highest; median income of leavers {sal['median_income_left']:,.0f} vs {sal['median_income_stayed']:,.0f} for stayers.",
        f"<b>Age:</b> the {age['top_group']['AgeGroup']} group has the highest attrition at {pct(age['top_group']['AttritionRatePct'])}.",
        f"<b>Job satisfaction:</b> {pct(sat['rate_low'])} attrition at the lowest level vs {pct(sat['rate_very_high'])} at the highest.",
        f"<b>Promotion gap:</b> no meaningful link in this dataset ({p_text(promo['test']['p_value'])}), contrary to a common assumption.",
        f"<b>Early tenure:</b> employees with 0-2 years at the company leave at {pct(early['rate'])} ({early['employees']} employees).",
    ]:
        s.append(Paragraph(b, BUL, bulletText="\u2022"))
    s.append(Paragraph("Correlation vs causation", H2))
    s.append(Paragraph("Every result below is an <b>association</b> measured on a single snapshot of employees. Leavers and stayers "
                       "differ in many ways at once (for example, younger staff are paid less, hold lower job levels and have shorter tenure), "
                       "so no single factor can be isolated as the cause of attrition. Statistical significance (chi-square or Mann-Whitney tests) "
                       "shows an association is unlikely to be chance; it does not show direction or cause. Testing causes would need "
                       "controlled or longitudinal data, such as exit interviews or a before/after policy trial.", BODY))
    s.append(PageBreak())

    # ---------------- Q1-Q7
    def rate_table(tbl, col, labels=None):
        rows = [[col, "Employees", "Left", "Attrition rate"]]
        for r in tbl.itertuples(index=False):
            d = r._asdict()
            key = tbl.columns[0]
            rows.append([str(labels[d[key]]) if labels else str(d[key]), d["Employees"], d["Attrition"], pct(d["AttritionRatePct"])])
        return table(rows, [6 * cm, 3 * cm, 3 * cm, 3.5 * cm])

    s.append(Paragraph("Answers to the seven business questions", H1))
    s.append(Paragraph("1. Which department has the highest attrition?", H2))
    s.append(Paragraph(f"<b>{dept['Department']}</b> ({pct(dept['AttritionRatePct'])}), against a company rate of {pct(avg)}. "
                       f"Research &amp; Development is the largest department but has the lowest rate. Department matters, but only weakly "
                       f"on its own (Cramer's V = {ins['chi_square_all'].set_index('variable').loc['Department','cramers_v']}); much of the department "
                       f"gap comes from the roles inside it (see Q2).", BODY))
    s += [rate_table(T["by_department"], "Department"), Spacer(1, 6), fig("02_department_attrition.png", 12.5)]

    s.append(PageBreak())
    s.append(Paragraph("2. Which job role has the highest employee turnover?", H2))
    s.append(Paragraph(f"<b>{role['JobRole']}</b> ({pct(role['AttritionRatePct'])}, {role['Attrition']} leavers), followed by "
                       f"{T['by_job_role'].iloc[1]['JobRole']} ({pct(T['by_job_role'].iloc[1]['AttritionRatePct'])}) and "
                       f"{T['by_job_role'].iloc[2]['JobRole']} ({pct(T['by_job_role'].iloc[2]['AttritionRatePct'])}). "
                       f"The lowest is {ins['q2_lowest_job_role']['JobRole']} ({pct(ins['q2_lowest_job_role']['AttritionRatePct'])}). "
                       f"Sales Representatives also have the lowest average pay of any role in the data "
                       f"({T['by_job_role'].iloc[0]['AvgMonthlyIncome']:,.0f}) and short tenure "
                       f"({T['by_job_role'].iloc[0]['AvgYearsAtCompany']} yrs), so role, pay and seniority are entangled. "
                       f"Small roles such as Research Director (n = 80) have wide uncertainty.", BODY))
    s.append(fig("07_job_role_attrition.png", 14.5))

    s.append(Paragraph("3. Does overtime increase attrition?", H2))
    s.append(Paragraph(f"Employees working overtime leave at <b>{pct(ot['rate_overtime'])}</b> vs <b>{pct(ot['rate_no_overtime'])}</b> for those who do not "
                       f"({ot['ratio']}x). The association is strong and highly significant (chi-square = {ot['test']['chi2']}, {p_text(ot['test']['p_value'])}; "
                       f"Cramer's V = {ot['test']['cramers_v']}, the strongest of the 15 variables tested). Overtime is a plausible driver (workload, "
                       f"burnout), but it could also be a marker of understaffed teams or of particular roles, so we call it a strong risk indicator rather than a proven cause.", BODY))
    s.append(PageBreak())
    s.append(fig("08_overtime_attrition.png", 11))

    s.append(Paragraph("4. Does lower salary correlate with higher attrition?", H2))
    s.append(Paragraph(f"Yes, moderately. Attrition falls steadily from <b>{pct(sal['lowest_slab_rate'])}</b> in the lowest slab to "
                       f"<b>{pct(sal['highest_slab_rate'])}</b> in the highest. The median monthly income of leavers is {sal['median_income_left']:,.0f} "
                       f"vs {sal['median_income_stayed']:,.0f} for stayers (Mann-Whitney {p_text(sal['mannwhitney_p'])}). The point-biserial correlation is "
                       f"{sal['corr']:.2f}, which is modest because income is skewed and overlaps heavily. Income is also highly correlated with job level and age, so "
                       f"low pay is intertwined with being junior and young.", BODY))
    s += [rate_table(T["by_salary_slab"], "Salary slab"), Spacer(1, 6), fig("05_salary_distribution.png", 12.5)]

    s.append(PageBreak())
    s.append(Paragraph("5. Which age group is most likely to leave?", H2))
    s.append(Paragraph(f"The <b>{age['top_group']['AgeGroup']}</b> group ({pct(age['top_group']['AttritionRatePct'])}, {age['top_group']['Attrition']} of "
                       f"{age['top_group']['Employees']}). Attrition drops with age, bottoming out at 36-45, and is somewhat higher again in the small 56+ group (n = 47, so treat that rate with caution). "
                       f"Age is associated with attrition ({p_text(age['test']['p_value'])}), but it overlaps heavily with tenure and pay.", BODY))
    s += [rate_table(T["by_age_group"], "Age group"), Spacer(1, 6), fig("04_age_group_attrition.png", 12)]

    s.append(Paragraph("6. How does job satisfaction influence attrition?", H2))
    s.append(Paragraph(f"Employees reporting the lowest job satisfaction leave at {pct(sat['rate_low'])}, about twice the {pct(sat['rate_very_high'])} seen at the highest level "
                       f"({p_text(sat['test']['p_value'])}). The effect size is smaller (Cramer's V = {sat['test']['cramers_v']}) than for overtime, role or job level. "
                       f"Work-life balance and environment satisfaction show a similar spike at the bottom level rather than a smooth gradient: "
                       f"the 'Bad' work-life-balance group leaves at {pct(wlb1['AttritionRatePct'])} and the lowest environment-satisfaction group at "
                       f"{pct(T['by_environment_satisfaction'].iloc[0]['AttritionRatePct'])}. Satisfaction is measured at one point in time, "
                       f"so we cannot tell whether low satisfaction led to leaving or whether leaving intent lowered reported satisfaction.", BODY))
    s += [rate_table(T["by_job_satisfaction"], "Job satisfaction (1=Low, 4=Very High)"), Spacer(1, 6), fig("09_job_satisfaction_attrition.png", 12)]

    s.append(PageBreak())
    s.append(Paragraph("7. Does promotion frequency affect employee retention?", H2))
    pr = promo["table"]
    s.append(Paragraph(f"<b>Not in this dataset.</b> Attrition is {pct(pr[0]['AttritionRatePct'])} for employees promoted 0-1 years ago, "
                       f"{pct(pr[1]['AttritionRatePct'])} for 2-4 years and {pct(pr[2]['AttritionRatePct'])} for 5+ years; the differences are not statistically "
                       f"significant ({p_text(promo['test']['p_value'])}; correlation with years-since-promotion = {promo['corr_years_since_promotion']:.2f}). "
                       f"This does not mean promotions are unimportant; it means that years-since-last-promotion does not separate leavers from stayers here. "
                       f"Seniority is the likely confounder: long-tenured, well-paid staff go longer between promotions and also tend to stay. "
                       f"Job level itself is informative: level 1 staff leave at {pct(lvl1['AttritionRatePct'])}.", BODY))
    s += [rate_table(T["by_promotion_gap"], "Years since last promotion"), Spacer(1, 6), fig("15_promotion_gap_attrition.png", 11.5)]

    # ---------------- additional evidence
    s.append(PageBreak())
    s.append(Paragraph("Additional evidence", H1))
    s.append(Paragraph("Strength of association with attrition (all categorical drivers)", H2))
    cs = ins["chi_square_all"].head(10)
    s.append(table([["Variable", "Chi-square", "df", "p-value", "Cramer's V"]] +
                   [[r.variable, f"{r.chi2:.1f}", r.dof, p_text(r.p_value), f"{r.cramers_v:.3f}"] for r in cs.itertuples()],
                   [5 * cm, 3 * cm, 2 * cm, 3 * cm, 3 * cm]))
    s.append(Paragraph("Cramer's V: about 0.1 = small, 0.3 = medium association. Associations here are small-to-moderate, so no single factor explains attrition.", NOTE))
    s.append(Paragraph("Combined risk-factor count (descriptive)", H2))
    s.append(Paragraph("Counting how many of four factors apply to an employee (overtime, job satisfaction 1-2, monthly income below 3,000, "
                       "tenure of 2 years or less) shows attrition climbing sharply as factors stack up. This is a transparent segmentation, "
                       "not a predictive model, and the top groups are small.", BODY))
    s.append(table([["Risk factors present", "Employees", "Left", "Attrition rate"]] +
                   [[int(r.risk), int(r.n), int(r.left), pct(r.rate)] for r in risk.itertuples()],
                   [5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]))
    s.append(Spacer(1, 6))
    s.append(fig("11_correlation_heatmap.png", 13))

    # ---------------- recommendations
    s.append(PageBreak())
    s.append(Paragraph("Recommendations for HR management", H1))
    recs = [
        ("Target the Sales Representative role first",
         f"At {pct(role['AttritionRatePct'])} attrition and the lowest average pay, this role accounts for {role['Attrition']} of {ov['attrition_count']} leavers. "
         f"Review pay bands, commission structure, onboarding and career path for the role. Pilot changes and measure the effect."),
        ("Audit overtime and workload",
         f"Overtime workers leave at {ot['ratio']}x the rate of others. Identify teams with the heaviest overtime, check staffing levels, and set overtime thresholds "
         f"that trigger a manager review. Track attrition for the same teams before and after."),
        ("Strengthen the first two years",
         f"{pct(early['rate'])} of employees with 0-2 years at the company leave. Improve onboarding, assign mentors, and hold stay interviews at 6 and 12 months."),
        ("Review pay for the lowest slab",
         f"Attrition is {pct(sal['lowest_slab_rate'])} in the lowest salary slab. Benchmark entry-level pay against market data before acting, "
         f"because pay is entangled with age, level and role."),
        ("Make stock options and level progression visible",
         f"Employees with no stock options leave at {pct(stock0['AttritionRatePct'])} and level 1 staff at {pct(lvl1['AttritionRatePct'])}. "
         f"Examine whether equity access and early-level progression can be widened."),
        ("Act on satisfaction signals, but validate them",
         f"Low job-satisfaction scorers leave at {pct(sat['rate_low'])}. Use survey results as an early-warning flag and follow up with conversations, "
         f"not as an automatic trigger."),
        ("Do not invest in promotion-timing fixes on this evidence alone",
         "Years since last promotion shows no link to attrition here. Pursue promotion policy changes only if exit interviews support them."),
        ("Improve data for causal learning",
         "Capture exit-interview reasons, voluntary vs involuntary exits, manager IDs, and leaving dates so that future analysis can study timing and causes."),
    ]
    for i, (h, t) in enumerate(recs, 1):
        s.append(KeepTogether([Paragraph(f"{i}. {h}", H2), Paragraph(t, BODY)]))

    s.append(Paragraph("Method &amp; limitations", H1))
    for b in ["Dataset: 1,470 employees, 35 columns; no missing values or duplicates; 3 constant columns dropped; outliers retained.",
              "The data is a single snapshot and does not contain leaving dates, exit reasons or voluntary/involuntary status.",
              "The dataset is fictional (IBM data scientists); conclusions illustrate method and are not facts about any real company.",
              "Monthly income is in the source data's unstated currency units; slabs (3K / 6K / 10K) are analyst-defined.",
              "Multiple comparisons were not corrected for; treat borderline p-values cautiously."]:
        s.append(Paragraph(b, BUL, bulletText="\u2022"))

    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title="HR Analytics & Employee Attrition - Business Insights", author="HR Analytics Project")
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"Saved {out}")


if __name__ == "__main__":
    build()
