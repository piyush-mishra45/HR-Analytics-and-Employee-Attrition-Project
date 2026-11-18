"""
HR Analytics & Employee Attrition - Streamlit dashboard.

Run from the project root:
    streamlit run dashboard/app.py

Features: upload an HR dataset (raw IBM CSV or the cleaned CSV), KPIs, filters by department / job role /
overtime, interactive Plotly charts, satisfaction analysis, and downloads of the cleaned dataset and
the analysis tables (Excel or ZIP of CSVs).
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import config as cfg                      # noqa: E402
import dashboard_utils as du              # noqa: E402
import eda_analysis as eda                # noqa: E402

NAVY, BLUE, RED = cfg.NAVY, cfg.BLUE, cfg.RED
COLORS = {"No": BLUE, "Yes": RED}

st.set_page_config(page_title="HR Analytics & Attrition Insights", page_icon="📊", layout="wide")
st.markdown(f"""
<style>
.block-container {{padding-top: 1.2rem;}}
.hero {{background:{NAVY};color:white;padding:18px 24px;border-radius:10px;margin-bottom:14px;}}
.hero h1 {{color:white;font-size:1.6rem;margin:0;}}
.hero p {{color:#B8C7DE;margin:4px 0 0 0;font-size:.9rem;}}
[data-testid="stMetric"] {{background:#F4F6FA;border-left:5px solid {BLUE};padding:10px 14px;border-radius:8px;}}
</style>
<div class="hero"><h1>HR ANALYTICS &amp; EMPLOYEE ATTRITION INSIGHTS</h1>
<p>IBM HR Analytics dataset (fictional). Charts show associations, not proven causes.</p></div>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_default() -> pd.DataFrame:
    return du.prepare_dataframe(du.read_upload(cfg.RAW_CSV))


# ------------------------------------------------------------------ data input
st.sidebar.header("Data")
upload = st.sidebar.file_uploader("Upload HR dataset (CSV)", type="csv",
                                  help="Raw IBM HR attrition CSV or the cleaned version.")
try:
    data = du.prepare_dataframe(du.read_upload(upload)) if upload else load_default()
    st.sidebar.caption(f"Source: {'uploaded file' if upload else 'bundled IBM sample'} ({len(data):,} rows)")
except Exception as exc:  # noqa: BLE001
    st.sidebar.error(f"Could not use this file: {exc}")
    st.stop()

st.sidebar.header("Filters")
dept_sel = st.sidebar.multiselect("Department", sorted(data["Department"].unique()))
role_pool = sorted(data[data["Department"].isin(dept_sel)]["JobRole"].unique()) if dept_sel else sorted(data["JobRole"].unique())
role_sel = st.sidebar.multiselect("Job role", role_pool)
ot_sel = st.sidebar.radio("Overtime", ["All", "Yes", "No"], horizontal=True)
df = du.filter_frame(data, dept_sel, role_sel, ot_sel)

if df.empty:
    st.warning("No employees match the current filters.")
    st.stop()

# ------------------------------------------------------------------------ KPIs
k = du.kpis(df)
c = st.columns(6)
c[0].metric("Total Employees", f"{k['total']:,}")
c[1].metric("Active Employees", f"{k['active']:,}")
c[2].metric("Attrition Count", f"{k['left']:,}")
c[3].metric("Attrition Rate", f"{k['rate']:.1f}%")
c[4].metric("Avg Age", f"{k['avg_age']:.1f}")
c[5].metric("Avg Monthly Income", f"{k['avg_income']:,.0f}")

T = eda.summary_tables(df)


def rate_bar(tbl, x, title, horizontal=False):
    """Attrition-rate bar chart with employees / leavers in the hover."""
    fig = px.bar(tbl, x="AttritionRatePct" if horizontal else x, y=x if horizontal else "AttritionRatePct",
                 orientation="h" if horizontal else "v", text="AttritionRatePct",
                 hover_data={"Employees": True, "Attrition": True}, title=title,
                 color_discrete_sequence=[BLUE])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(plot_bgcolor="white", margin=dict(t=50, b=10), yaxis_title=None if horizontal else "Attrition rate (%)",
                      xaxis_title="Attrition rate (%)" if horizontal else None)
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    return fig


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Attrition Drivers", "Satisfaction", "Department", "Data & Export"])

with tab1:
    a, b = st.columns(2)
    status = df["Attrition"].value_counts().rename_axis("Attrition").reset_index(name="Employees")
    fig = px.pie(status, names="Attrition", values="Employees", hole=0.55, color="Attrition",
                 color_discrete_map=COLORS, title="Active (No) vs Attrition (Yes)")
    a.plotly_chart(fig, use_container_width=True)
    b.plotly_chart(rate_bar(T["by_department"], "Department", "Attrition Rate by Department"), use_container_width=True)
    a, b = st.columns(2)
    a.plotly_chart(rate_bar(T["by_gender"], "Gender", "Attrition Rate by Gender"), use_container_width=True)
    b.plotly_chart(rate_bar(T["by_age_group"], "AgeGroup", "Attrition Rate by Age Group"), use_container_width=True)

with tab2:
    a, b = st.columns(2)
    a.plotly_chart(rate_bar(T["by_job_role"], "JobRole", "Attrition Rate by Job Role", horizontal=True), use_container_width=True)
    b.plotly_chart(rate_bar(T["by_overtime"], "OverTime", "Attrition Rate by Overtime"), use_container_width=True)
    a, b = st.columns(2)
    a.plotly_chart(rate_bar(T["by_salary_slab"], "SalarySlab", "Attrition Rate by Salary Slab"), use_container_width=True)
    b.plotly_chart(rate_bar(T["by_tenure_band"], "TenureBand", "Attrition Rate by Years at Company"), use_container_width=True)
    a, b = st.columns(2)
    a.plotly_chart(rate_bar(T["by_business_travel"], "BusinessTravel", "Attrition Rate by Business Travel"), use_container_width=True)
    b.plotly_chart(rate_bar(T["by_job_level"].astype({"JobLevel": str}), "JobLevel", "Attrition Rate by Job Level"), use_container_width=True)
    st.caption("Associations only: these patterns do not prove that any single factor causes attrition.")

with tab3:
    sat_map = {1: "1 Low", 2: "2 Medium", 3: "3 High", 4: "4 Very High"}
    wlb_map = {1: "1 Bad", 2: "2 Good", 3: "3 Better", 4: "4 Best"}
    a, b = st.columns(2)
    for col, key, title, mp in [(a, "by_job_satisfaction", "Job Satisfaction", sat_map),
                                (b, "by_environment_satisfaction", "Environment Satisfaction", sat_map),
                                (a, "by_work_life_balance", "Work-Life Balance", wlb_map),
                                (b, "by_relationship_satisfaction", "Relationship Satisfaction", sat_map)]:
        t = T[key].copy()
        t[t.columns[0]] = t[t.columns[0]].map(mp)
        col.plotly_chart(rate_bar(t, t.columns[0], f"Attrition Rate by {title}"), use_container_width=True)
    st.subheader("Average scores: leavers vs active")
    scores = df.groupby("Attrition")[["JobSatisfaction", "EnvironmentSatisfaction", "WorkLifeBalance",
                                      "RelationshipSatisfaction", "JobInvolvement"]].mean().round(2)
    st.dataframe(scores, use_container_width=True)

with tab4:
    dept_tbl = T["by_department"]
    a, b = st.columns(2)
    a.plotly_chart(px.bar(dept_tbl, x="Department", y="Employees", title="Employees by Department",
                          color_discrete_sequence=[NAVY]), use_container_width=True)
    b.plotly_chart(px.bar(dept_tbl, x="Department", y="AvgMonthlyIncome", title="Average Monthly Income by Department",
                          color_discrete_sequence=[BLUE]), use_container_width=True)
    a, b = st.columns(2)
    a.plotly_chart(px.bar(dept_tbl, x="Department", y="AvgYearsAtCompany", title="Average Years at Company",
                          color_discrete_sequence=[BLUE]), use_container_width=True)
    roles = df.groupby(["Department", "JobRole"]).size().reset_index(name="Employees")
    b.plotly_chart(px.treemap(roles, path=["Department", "JobRole"], values="Employees", title="Job Role Distribution"),
                   use_container_width=True)

with tab5:
    st.subheader("Preview")
    st.dataframe(df.head(200), use_container_width=True)
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇ Cleaned dataset (CSV, filtered)", df.to_csv(index=False).encode("utf-8"),
                       file_name="hr_attrition_cleaned.csv", mime="text/csv")
    d2.download_button("⬇ Analysis results (Excel)", du.results_workbook(df), file_name="attrition_analysis_results.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d3.download_button("⬇ Analysis tables (ZIP of CSVs)", du.results_zip(df), file_name="attrition_analysis_tables.zip",
                       mime="application/zip")
