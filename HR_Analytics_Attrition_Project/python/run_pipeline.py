"""
Run the whole workflow, raw CSV -> cleaned data -> tables -> figures -> SQL -> Excel -> PDF -> notebooks.

Usage (from the project root):
    python python/run_pipeline.py
"""
from __future__ import annotations

import time

import build_excel
import build_notebooks
import data_cleaning
import eda_analysis
import generate_report
import generate_sql_inserts
import validate_sql
import visualization


def step(name, fn):
    t = time.time()
    print(f"\n=== {name} ===")
    out = fn()
    print(f"--- done in {time.time() - t:.1f}s")
    return out


def main() -> None:
    step("1. Clean data", data_cleaning.run)
    step("2. EDA tables & statistics", eda_analysis.run)
    step("3. Figures", visualization.generate_all)
    step("4. SQL insert script", generate_sql_inserts.run)
    ok = step("5. Validate SQL (SQLite + pandas cross-check)", validate_sql.run)
    step("6. Excel workbook", build_excel.build)
    step("7. Business insights PDF", generate_report.build)
    step("8. Notebooks", build_notebooks.run)
    print("\nPipeline finished." + ("" if ok else "  WARNING: SQL validation reported problems."))
    print("Next: open excel/HR_Analytics_Report.xlsx, run `streamlit run dashboard/app.py`, build the Power BI file (see powerbi/).")


if __name__ == "__main__":
    main()
