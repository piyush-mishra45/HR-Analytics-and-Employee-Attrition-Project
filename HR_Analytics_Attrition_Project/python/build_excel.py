"""
Build excel/HR_Analytics_Report.xlsx with openpyxl.

Every number on the analysis sheets is a live Excel formula (COUNTIF / COUNTIFS / AVERAGEIF /
AVERAGEIFS / IF / VLOOKUP / INDEX-MATCH) pointing at the Cleaned_Data sheet, so the workbook
recalculates if the data changes.

NOTE: openpyxl cannot create native PivotTables. The formula-driven summary tables below play
that role, and native Excel charts are used in place of PivotCharts. To add true PivotTables,
select Cleaned_Data -> Insert -> PivotTable in Excel (steps in docs/SETUP_GUIDE.md).

Usage
-----
    python python/build_excel.py
"""
from __future__ import annotations

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

import config as cfg
import data_cleaning as dc

FONT = "Arial"
NAVY, BLUE, LIGHT, WHITE = "0B1F3A", "2E6FBA", "EAF0F8", "FFFFFF"
f_title = Font(name=FONT, size=16, bold=True, color=WHITE)
f_head = Font(name=FONT, size=10, bold=True, color=WHITE)
f_body = Font(name=FONT, size=10)
f_bold = Font(name=FONT, size=10, bold=True)
f_input = Font(name=FONT, size=10, color="0000FF", bold=True)   # blue = user-editable input
f_note = Font(name=FONT, size=9, italic=True, color="5A6475")
fill_navy = PatternFill("solid", fgColor=NAVY)
fill_blue = PatternFill("solid", fgColor=BLUE)
fill_light = PatternFill("solid", fgColor=LIGHT)
fill_input = PatternFill("solid", fgColor="FFF8DC")
thin = Side(style="thin", color="C9D1DE")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

FMT_INT, FMT_PCT, FMT_DEC = "#,##0", "0.0%", "#,##0.0"


class Ctx:
    """Holds the cleaned dataframe and column -> range helper for formulas."""

    def __init__(self, clean: pd.DataFrame):
        self.cols = list(clean.columns)
        self.n = len(clean)

    def rng(self, col: str) -> str:
        letter = L(self.cols.index(col) + 1)
        return f"Cleaned_Data!${letter}$2:${letter}${self.n + 1}"


# --------------------------------------------------------------------- helpers
def write_df(ws, df: pd.DataFrame) -> None:
    ws.append(list(df.columns))
    for row in df.itertuples(index=False):
        ws.append(list(row))
    for c in ws[1]:
        c.font, c.fill, c.alignment = f_head, fill_navy, CENTER
    for col in range(1, len(df.columns) + 1):
        ws.column_dimensions[L(col)].width = max(12, min(26, len(str(df.columns[col - 1])) + 3))
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = True


def sheet_title(ws, text: str, sub: str, width_cols: int = 8) -> None:
    ws.sheet_view.showGridLines = False
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=width_cols)
    ws["A1"] = text
    ws["A1"].font, ws["A1"].fill = f_title, fill_navy
    ws["A1"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 30
    ws["A2"] = sub
    ws["A2"].font = f_note


def header_row(ws, row: int, headers: list[str]) -> None:
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font, c.fill, c.alignment, c.border = f_head, fill_blue, CENTER, box


def style_cell(c, fmt=None, bold=False) -> None:
    c.font = f_bold if bold else f_body
    c.border = box
    if fmt:
        c.number_format = fmt


def dim_block(ws, ctx: Ctx, top: int, title: str, col: str, cats: list, first_header: str,
              extras: list | None = None, chart_title: str | None = None,
              chart_anchor: str | None = None, min_height: int = 16) -> dict:
    """
    Write a formula-driven summary table for one dimension.
    Columns: category | Employees | Leavers | Active | Attrition Rate | % of All Leavers | extras...
    Returns dict with row positions for later reference.
    """
    extras = extras or []
    ws.cell(row=top, column=1, value=title).font = Font(name=FONT, size=12, bold=True, color=NAVY)
    headers = [first_header, "Employees", "Leavers", "Active", "Attrition Rate", "% of All Leavers"]
    headers += [e[0] for e in extras]
    header_row(ws, top + 1, headers)
    first = top + 2
    last = first + len(cats) - 1
    for i, cat in enumerate(cats):
        r = first + i
        a = ws.cell(row=r, column=1, value=cat)
        style_cell(a, bold=True)
        a.alignment = Alignment(horizontal="left")
        style_cell(ws.cell(row=r, column=2, value=f"=COUNTIF({ctx.rng(col)},$A{r})"), FMT_INT)
        style_cell(ws.cell(row=r, column=3,
                           value=f'=COUNTIFS({ctx.rng(col)},$A{r},{ctx.rng("Attrition")},"Yes")'), FMT_INT)
        style_cell(ws.cell(row=r, column=4, value=f"=B{r}-C{r}"), FMT_INT)
        style_cell(ws.cell(row=r, column=5, value=f"=IF(B{r}=0,0,C{r}/B{r})"), FMT_PCT)
        style_cell(ws.cell(row=r, column=6, value=f"=IF(KPI_Summary!$F$5=0,0,C{r}/KPI_Summary!$F$5)"), FMT_PCT)
        for j, (_, fn, fmt) in enumerate(extras):
            style_cell(ws.cell(row=r, column=7 + j, value=fn(r, first, last)), fmt)
    tr = last + 1
    style_cell(ws.cell(row=tr, column=1, value="Total"), bold=True)
    for c_idx, fmt in [(2, FMT_INT), (3, FMT_INT), (4, FMT_INT)]:
        style_cell(ws.cell(row=tr, column=c_idx, value=f"=SUM({L(c_idx)}{first}:{L(c_idx)}{last})"), fmt, True)
    style_cell(ws.cell(row=tr, column=5, value=f"=IF(B{tr}=0,0,C{tr}/B{tr})"), FMT_PCT, True)
    style_cell(ws.cell(row=tr, column=6, value=f"=SUM(F{first}:F{last})"), FMT_PCT, True)
    for c_idx in range(1, 7 + len(extras)):
        ws.cell(row=tr, column=c_idx).fill = fill_light
    # conditional formatting
    ws.conditional_formatting.add(f"E{first}:E{last}", ColorScaleRule(
        start_type="min", start_color="D9E8F7", mid_type="percentile", mid_value=50,
        mid_color="FFF2CC", end_type="max", end_color="F4A6A6"))
    ws.conditional_formatting.add(f"B{first}:B{last}", DataBarRule(
        start_type="num", start_value=0, end_type="max", color="8FB8E8"))
    ws.conditional_formatting.add(f"A{first}:A{last}", FormulaRule(
        formula=[f"$E{first}>KPI_Summary!$H$5"], font=Font(name=FONT, bold=True, color="B42318")))
    if chart_title:
        ch = BarChart()
        ch.type, ch.style, ch.title = "col", 10, chart_title
        ch.add_data(Reference(ws, min_col=5, min_row=top + 1, max_row=last), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
        ch.y_axis.number_format = "0%"
        ch.y_axis.title = "Attrition rate"
        ch.legend = None
        ch.roundedCorners = False
        ch.x_axis.delete = False
        ch.y_axis.delete = False
        ch.dataLabels = DataLabelList()
        ch.dataLabels.showVal = True
        ch.series[0].graphicalProperties.solidFill = BLUE
        ch.height, ch.width = 7.5, 15
        ws.add_chart(ch, chart_anchor or f"{L(9 + len(extras))}{top}")
    return {"first": first, "last": last, "total": tr, "next": top + max(len(cats) + 4, min_height)}


# ------------------------------------------------------------------- sheets
def build_attrition(ws, ctx: Ctx, df: pd.DataFrame) -> dict:
    sheet_title(ws, "ATTRITION ANALYSIS", "Formula-driven summaries of Cleaned_Data. Red bold label = rate above company average.", 14)
    pos, top = {}, 4
    specs = [
        ("gender", "Attrition by Gender", "Gender", sorted(df.Gender.unique()), "Gender"),
        ("age", "Attrition by Age Group", "AgeGroup", cfg.AGE_LABELS, "Age group"),
        ("overtime", "Attrition by Overtime", "OverTime", ["Yes", "No"], "Overtime"),
        ("travel", "Attrition by Business Travel", "BusinessTravel",
         ["Non-Travel", "Travel_Rarely", "Travel_Frequently"], "Business travel"),
        ("marital", "Attrition by Marital Status", "MaritalStatus", sorted(df.MaritalStatus.unique()), "Marital status"),
        ("role", "Attrition by Job Role", "JobRole", sorted(df.JobRole.unique()), "Job role"),
        ("level", "Attrition by Job Level", "JobLevel", [1, 2, 3, 4, 5], "Job level"),
        ("tenure", "Attrition by Years at Company", "TenureBand", cfg.TENURE_LABELS, "Tenure band"),
        ("promo", "Attrition by Years Since Last Promotion", "PromotionGap", cfg.PROMO_LABELS, "Years since promotion"),
    ]
    for key, title, col, cats, hdr in specs:
        pos[key] = dim_block(ws, ctx, top, title, col, cats, hdr, chart_title=title, chart_anchor=f"H{top}")
        top = pos[key]["next"]
    for c, w in zip("ABCDEFG", [26, 12, 11, 11, 15, 16, 4]):
        ws.column_dimensions[c].width = w
    return pos


def build_department(ws, ctx: Ctx, df: pd.DataFrame) -> dict:
    sheet_title(ws, "DEPARTMENT ANALYSIS", "Headcount, attrition, pay and experience by department.", 12)
    depts = sorted(df.Department.unique())
    extras = [
        ("Avg Monthly Income", lambda r, a, b: f"=AVERAGEIF({ctx.rng('Department')},$A{r},{ctx.rng('MonthlyIncome')})", FMT_INT),
        ("Avg Years at Company", lambda r, a, b: f"=AVERAGEIF({ctx.rng('Department')},$A{r},{ctx.rng('YearsAtCompany')})", "0.0"),
        ("Avg Total Working Yrs", lambda r, a, b: f"=AVERAGEIF({ctx.rng('Department')},$A{r},{ctx.rng('TotalWorkingYears')})", "0.0"),
        ("Overtime Share", lambda r, a, b: f'=IF(B{r}=0,0,COUNTIFS({ctx.rng("Department")},$A{r},{ctx.rng("OverTime")},"Yes")/B{r})', FMT_PCT),
        ("Attrition Rank", lambda r, a, b: f"=RANK(E{r},$E${a}:$E${b},0)", "0"),
    ]
    p = dim_block(ws, ctx, 4, "Department Summary", "Department", depts, "Department", extras,
                  "Attrition Rate by Department", "A13")
    # Job role x department headcount matrix
    top = 31
    ws.cell(row=top, column=1, value="Job Role Distribution by Department (headcount)").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    header_row(ws, top + 1, ["Job role"] + depts + ["Total"])
    roles = sorted(df.JobRole.unique())
    for i, role in enumerate(roles):
        r = top + 2 + i
        style_cell(ws.cell(row=r, column=1, value=role), bold=True)
        for j, d in enumerate(depts):
            hdr_cell = f"{L(2 + j)}${top + 1}"
            style_cell(ws.cell(row=r, column=2 + j,
                               value=f"=COUNTIFS({ctx.rng('JobRole')},$A{r},{ctx.rng('Department')},{hdr_cell})"), FMT_INT)
        style_cell(ws.cell(row=r, column=2 + len(depts), value=f"=SUM(B{r}:{L(1 + len(depts))}{r})"), FMT_INT, True)
    ws.conditional_formatting.add(f"B{top + 2}:{L(1 + len(depts))}{top + 1 + len(roles)}", ColorScaleRule(
        start_type="min", start_color="FFFFFF", end_type="max", end_color="5B9BD5"))
    ws.column_dimensions["A"].width = 28
    for c in "BCDEFGHIJKL":
        ws.column_dimensions[c].width = 16
    return p


def build_salary(ws, ctx: Ctx, df: pd.DataFrame) -> dict:
    sheet_title(ws, "SALARY ANALYSIS", "Monthly income in the source data's currency units (the IBM dataset does not state a currency).", 12)
    extras = [("Avg Monthly Income", lambda r, a, b: f"=AVERAGEIF({ctx.rng('SalarySlab')},$A{r},{ctx.rng('MonthlyIncome')})", FMT_INT)]
    p = dim_block(ws, ctx, 4, "Attrition by Salary Slab", "SalarySlab", cfg.SALARY_LABELS, "Salary slab",
                  extras, "Attrition Rate by Salary Slab", "I4")
    top = 22
    ws.cell(row=top, column=1, value="Income & Pay Metrics: Leavers vs Active").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    header_row(ws, top + 1, ["Status", "Employees", "Avg Monthly Income", "Avg % Salary Hike", "Avg Job Level", "Avg Total Working Yrs"])
    for i, (lab, key) in enumerate([("Left", "Yes"), ("Active", "No")]):
        r = top + 2 + i
        style_cell(ws.cell(row=r, column=1, value=lab), bold=True)
        crit = f'"{key}"'
        style_cell(ws.cell(row=r, column=2, value=f"=COUNTIF({ctx.rng('Attrition')},{crit})"), FMT_INT)
        style_cell(ws.cell(row=r, column=3, value=f"=AVERAGEIF({ctx.rng('Attrition')},{crit},{ctx.rng('MonthlyIncome')})"), FMT_INT)
        style_cell(ws.cell(row=r, column=4, value=f"=AVERAGEIF({ctx.rng('Attrition')},{crit},{ctx.rng('PercentSalaryHike')})"), "0.0")
        style_cell(ws.cell(row=r, column=5, value=f"=AVERAGEIF({ctx.rng('Attrition')},{crit},{ctx.rng('JobLevel')})"), "0.00")
        style_cell(ws.cell(row=r, column=6, value=f"=AVERAGEIF({ctx.rng('Attrition')},{crit},{ctx.rng('TotalWorkingYears')})"), "0.0")
    r = top + 4
    style_cell(ws.cell(row=r, column=1, value="Income gap (Active - Left)"), bold=True)
    style_cell(ws.cell(row=r, column=3, value=f"=C{top + 3}-C{top + 2}"), FMT_INT, True)
    style_cell(ws.cell(row=r, column=4, value=f'=IF(C{r}>0,"Leavers earn less on average","Leavers earn the same or more")'))
    ws.cell(row=r + 1, column=1, value="Association only: lower pay and attrition move together here; this sheet does not prove pay causes exits.").font = f_note
    ext2 = [("Avg Monthly Income", lambda r, a, b: f"=AVERAGEIF({ctx.rng('JobLevel')},$A{r},{ctx.rng('MonthlyIncome')})", FMT_INT)]
    dim_block(ws, ctx, 31, "Attrition by Job Level (with average pay)", "JobLevel", [1, 2, 3, 4, 5], "Job level", ext2, "Attrition Rate by Job Level", "I31")
    ws.column_dimensions["A"].width = 30
    for c in "BCDEFGH":
        ws.column_dimensions[c].width = 17
    return p


def build_satisfaction(ws, ctx: Ctx, df: pd.DataFrame) -> dict:
    sheet_title(ws, "EMPLOYEE SATISFACTION", "Survey scale 1-4. Attrition rate for each satisfaction level.", 12)
    top, pos = 4, {}
    sat_labels = '"Low","Medium","High","Very High"'
    wlb_labels = '"Bad","Good","Better","Best"'
    specs = [
        ("job", "Job Satisfaction", "JobSatisfaction", sat_labels),
        ("env", "Environment Satisfaction", "EnvironmentSatisfaction", sat_labels),
        ("wlb", "Work-Life Balance", "WorkLifeBalance", wlb_labels),
        ("rel", "Relationship Satisfaction", "RelationshipSatisfaction", sat_labels),
    ]
    for key, title, col, labs in specs:
        extras = [("Label", (lambda labs: lambda r, a, b: f"=CHOOSE($A{r},{labs})")(labs), None),
                  ("Avg Monthly Income", (lambda col: lambda r, a, b: f"=AVERAGEIF({ctx.rng(col)},$A{r},{ctx.rng('MonthlyIncome')})")(col), FMT_INT)]
        pos[key] = dim_block(ws, ctx, top, f"Attrition by {title}", col, [1, 2, 3, 4], "Level (1-4)", extras,
                             f"Attrition Rate by {title}", f"J{top}")
        top = pos[key]["next"]
    # average score leavers vs active
    ws.cell(row=top, column=1, value="Average satisfaction score: Leavers vs Active").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    header_row(ws, top + 1, ["Status", "Job Sat.", "Environment Sat.", "Work-Life Balance", "Relationship Sat.", "Job Involvement"])
    cols = ["JobSatisfaction", "EnvironmentSatisfaction", "WorkLifeBalance", "RelationshipSatisfaction", "JobInvolvement"]
    for i, (lab, key) in enumerate([("Left", "Yes"), ("Active", "No")]):
        r = top + 2 + i
        style_cell(ws.cell(row=r, column=1, value=lab), bold=True)
        for j, c in enumerate(cols):
            style_cell(ws.cell(row=r, column=2 + j,
                               value=f'=AVERAGEIF({ctx.rng("Attrition")},"{key}",{ctx.rng(c)})'), "0.00")
    ws.column_dimensions["A"].width = 26
    for c in "BCDEFGHI":
        ws.column_dimensions[c].width = 16
    pos["avg_top"] = top
    return pos


def build_kpi(ws, ctx: Ctx, df: pd.DataFrame, pa: dict, pd_: dict, ps: dict, psat: dict) -> None:
    sheet_title(ws, "HR ANALYTICS & EMPLOYEE ATTRITION: KPI SUMMARY", "All values are live formulas on Cleaned_Data. Blue cells on yellow are inputs you can change.", 9)
    for c in "ABCDEFGHI":
        ws.column_dimensions[c].width = 15
    ws.column_dimensions["A"].width = 3

    def card(row, col, label, formula, fmt):
        ws.merge_cells(start_row=row - 1, start_column=col, end_row=row - 1, end_column=col + 1)
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)
        lab = ws.cell(row=row - 1, column=col, value=label)
        lab.font, lab.fill, lab.alignment = Font(name=FONT, size=9, bold=True, color=WHITE), fill_blue, CENTER
        ws.cell(row=row - 1, column=col + 1).fill = fill_blue
        v = ws.cell(row=row, column=col, value=formula)
        v.font, v.fill, v.alignment, v.number_format = Font(name=FONT, size=18, bold=True, color=NAVY), fill_light, CENTER, fmt
        ws.cell(row=row, column=col + 1).fill = fill_light
        ws.row_dimensions[row].height = 34

    n = ctx.n + 1
    emp = ctx.rng("EmployeeNumber")
    att = ctx.rng("Attrition")
    # Row 5 cards: B5 total, D5 active... F5 must be Attrition Count and H5 Attrition Rate (referenced elsewhere)
    card(5, 2, "TOTAL EMPLOYEES", f"=COUNTA({emp})", FMT_INT)
    card(5, 4, "ACTIVE EMPLOYEES", f'=COUNTIF({att},"No")', FMT_INT)
    card(5, 6, "ATTRITION COUNT", f'=COUNTIF({att},"Yes")', FMT_INT)
    card(5, 8, "ATTRITION RATE", "=IF(B5=0,0,F5/B5)", FMT_PCT)
    card(9, 2, "AVERAGE AGE", f"=AVERAGE({ctx.rng('Age')})", "0.0")
    card(9, 4, "AVG MONTHLY INCOME", f"=AVERAGE({ctx.rng('MonthlyIncome')})", FMT_INT)
    card(9, 6, "AVG YEARS AT COMPANY", f"=AVERAGE({ctx.rng('YearsAtCompany')})", "0.0")
    card(9, 8, "OVERTIME SHARE", f'=COUNTIF({ctx.rng("OverTime")},"Yes")/B5', FMT_PCT)

    # Formula-driven findings
    r0 = 12
    ws.cell(row=r0, column=2, value="Key Findings (formula-driven)").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    heads = ["Finding", "", "", "Segment", "", "Rate", "vs Company", "Flag"]
    for i, h in enumerate(heads, start=2):
        c = ws.cell(row=r0 + 1, column=i, value=h)
        c.font, c.fill, c.alignment = f_head, fill_navy, CENTER

    def finding(row, label, seg_formula, rate_formula):
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=6)
        ws.cell(row=row, column=2, value=label).font = f_body
        ws.cell(row=row, column=5, value=seg_formula).font = f_bold
        ws.cell(row=row, column=7, value=rate_formula).number_format = FMT_PCT
        ws.cell(row=row, column=8, value=f"=G{row}-$H$5").number_format = '+0.0%;-0.0%;0.0%'
        ws.cell(row=row, column=9, value=f'=IF(G{row}>$H$5,"Above average","At/below average")')
        for c in range(2, 10):
            ws.cell(row=row, column=c).border = box
            if c in (7, 8, 9):
                ws.cell(row=row, column=c).font = f_body

    d, a_, s, sa = pd_, pa, ps, psat
    rng_dep_name = f"Department_Analysis!$A${d['first']}:$A${d['last']}"
    rng_dep_rate = f"Department_Analysis!$E${d['first']}:$E${d['last']}"
    finding(r0 + 2, "Department with highest attrition",
            f"=INDEX({rng_dep_name},MATCH(MAX({rng_dep_rate}),{rng_dep_rate},0))", f"=MAX({rng_dep_rate})")
    role_n = f"Attrition_Analysis!$A${a_['role']['first']}:$A${a_['role']['last']}"
    role_r = f"Attrition_Analysis!$E${a_['role']['first']}:$E${a_['role']['last']}"
    finding(r0 + 3, "Job role with highest attrition", f"=INDEX({role_n},MATCH(MAX({role_r}),{role_r},0))", f"=MAX({role_r})")
    age_n = f"Attrition_Analysis!$A${a_['age']['first']}:$A${a_['age']['last']}"
    age_r = f"Attrition_Analysis!$E${a_['age']['first']}:$E${a_['age']['last']}"
    finding(r0 + 4, "Age group with highest attrition", f"=INDEX({age_n},MATCH(MAX({age_r}),{age_r},0))", f"=MAX({age_r})")
    ot = a_["overtime"]["first"]
    finding(r0 + 5, "Employees working overtime", "Overtime = Yes", f"=Attrition_Analysis!E{ot}")
    finding(r0 + 6, "Employees not working overtime", "Overtime = No", f"=Attrition_Analysis!E{ot + 1}")
    finding(r0 + 7, "Lowest salary slab", f"=Salary_Analysis!A{s['first']}", f"=Salary_Analysis!E{s['first']}")
    finding(r0 + 8, "Highest salary slab", f"=Salary_Analysis!A{s['last']}", f"=Salary_Analysis!E{s['last']}")
    jb = psat["job"]["first"]
    finding(r0 + 9, "Lowest job satisfaction (level 1)", "Job satisfaction = 1", f"=Employee_Satisfaction!E{jb}")
    finding(r0 + 10, "Highest job satisfaction (level 4)", "Job satisfaction = 4", f"=Employee_Satisfaction!E{jb + 3}")
    ws.conditional_formatting.add(f"I{r0 + 2}:I{r0 + 10}", FormulaRule(
        formula=[f'I{r0 + 2}="Above average"'], font=Font(name=FONT, bold=True, color="B42318")))

    # Department lookup (VLOOKUP + IF)
    r1 = r0 + 13
    ws.cell(row=r1, column=2, value="Department Lookup (VLOOKUP)").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    ws.cell(row=r1 + 1, column=2, value="Choose department:").font = f_bold
    inp = ws.cell(row=r1 + 1, column=4, value=sorted(df.Department.unique())[-1])
    inp.font, inp.fill, inp.border = f_input, fill_input, box
    ws.merge_cells(start_row=r1 + 1, start_column=4, end_row=r1 + 1, end_column=5)
    dv = DataValidation(type="list", formula1='"' + ",".join(sorted(df.Department.unique())) + '"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(inp)
    tbl = f"Department_Analysis!$A${d['first']}:$K${d['last']}"
    for i, (lab, colidx, fmt) in enumerate([("Employees", 2, FMT_INT), ("Leavers", 3, FMT_INT), ("Attrition rate", 5, FMT_PCT),
                                             ("Avg monthly income", 7, FMT_INT), ("Avg years at company", 8, "0.0")]):
        r = r1 + 2 + i
        ws.cell(row=r, column=2, value=lab).font = f_body
        c = ws.cell(row=r, column=4, value=f"=VLOOKUP($D${r1 + 1},{tbl},{colidx},FALSE)")
        c.number_format, c.font = fmt, f_bold
    r = r1 + 7
    ws.cell(row=r, column=2, value="Status vs company:").font = f_body
    ws.cell(row=r, column=4, value=f'=IF(D{r1 + 4}>$H$5,"Above company attrition rate","At or below company rate")').font = f_bold

    # Employee lookup (INDEX/MATCH)
    r2 = r1 + 10
    ws.cell(row=r2, column=2, value="Employee Lookup (INDEX / MATCH)").font = Font(name=FONT, size=12, bold=True, color=NAVY)
    ws.cell(row=r2 + 1, column=2, value="Employee number:").font = f_bold
    e_in = ws.cell(row=r2 + 1, column=4, value=1)
    e_in.font, e_in.fill, e_in.border = f_input, fill_input, box
    for i, col in enumerate(["Department", "JobRole", "Age", "MonthlyIncome", "OverTime", "Attrition"]):
        r = r2 + 2 + i
        ws.cell(row=r, column=2, value=col).font = f_body
        c = ws.cell(row=r, column=4, value=f'=IFERROR(INDEX({ctx.rng(col)},MATCH($D${r2 + 1},{emp},0)),"Not found")')
        c.font = f_bold
        if col == "MonthlyIncome":
            c.number_format = FMT_INT
    notes = r2 + 9
    ws.cell(row=notes, column=2, value="Legend: blue text on yellow = editable input; everything else is a formula. Source: IBM HR Analytics Employee Attrition & Performance dataset (a fictional dataset created by IBM data scientists).").font = f_note
    ws.cell(row=notes + 1, column=2, value="Rates describe associations in this dataset and are not proof of cause.").font = f_note
    ws.freeze_panes = "A4"


def build(out=cfg.EXCEL_DIR / "HR_Analytics_Report.xlsx") -> None:
    raw = dc.load_raw()
    clean = pd.read_csv(cfg.CLEAN_CSV)
    ctx = Ctx(clean)
    wb = Workbook()
    ws_raw = wb.active
    ws_raw.title = "Raw_Data"
    write_df(ws_raw, raw)
    write_df(wb.create_sheet("Cleaned_Data"), clean)
    ws_a, ws_d = wb.create_sheet("Attrition_Analysis"), wb.create_sheet("Department_Analysis")
    ws_s, ws_sat, ws_k = wb.create_sheet("Salary_Analysis"), wb.create_sheet("Employee_Satisfaction"), wb.create_sheet("KPI_Summary")
    pa = build_attrition(ws_a, ctx, clean)
    pdp = build_department(ws_d, ctx, clean)
    ps = build_salary(ws_s, ctx, clean)
    psat = build_satisfaction(ws_sat, ctx, clean)
    build_kpi(ws_k, ctx, clean, pa, pdp, ps, psat)
    for ws, color in [(ws_a, BLUE), (ws_d, BLUE), (ws_s, BLUE), (ws_sat, BLUE), (ws_k, NAVY)]:
        ws.sheet_properties.tabColor = color
    wb.active = wb.sheetnames.index("KPI_Summary")
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    build()
