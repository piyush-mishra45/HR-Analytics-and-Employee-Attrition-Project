"""
Validate the SQL scripts without a MySQL server by executing them in SQLite
(which supports JOIN / CTE / window functions) and cross-checking results against pandas.

MySQL-only syntax (USE, ENGINE=, FOREIGN_KEY_CHECKS, TRUNCATE) is stripped / translated first.
NOTE: this proves the query LOGIC and numbers; it does not replace a run on a real MySQL 8 server.

Usage
-----
    python python/validate_sql.py
"""
from __future__ import annotations

import re
import sqlite3

import pandas as pd

import config as cfg


def to_sqlite(sql: str) -> str:
    sql = re.sub(r"^\s*USE\s+\w+;\s*$", "", sql, flags=re.M | re.I)
    sql = re.sub(r"\)\s*ENGINE=InnoDB;", ");", sql)
    sql = re.sub(r"^\s*SET FOREIGN_KEY_CHECKS\s*=\s*\d;\s*$", "", sql, flags=re.M)
    sql = re.sub(r"^\s*TRUNCATE TABLE \w+;\s*$", "", sql, flags=re.M)
    sql = sql.replace("TINYINT", "INTEGER")
    return sql


def split_queries(sql: str) -> list[tuple[str, str]]:
    blocks = re.split(r"^-- (Q\d+):", sql, flags=re.M)
    out = []
    for i in range(1, len(blocks), 2):
        title_and_body = blocks[i + 1]
        # first line is the remainder of the "-- Q<n>: title" header -> drop it
        lines = title_and_body.splitlines()[1:]
        body = "\n".join(l for l in lines
                         if not l.strip().startswith("-- ----") and not l.strip().startswith("-- SECTION"))
        out.append((blocks[i], body.strip()))
    return out


def run() -> bool:
    con = sqlite3.connect(":memory:")
    for f in ["create_tables.sql", "insert_data.sql"]:
        script = to_sqlite((cfg.SQL_DIR / f).read_text(encoding="utf-8"))
        con.executescript(script)

    queries = split_queries((cfg.SQL_DIR / "analysis_queries.sql").read_text(encoding="utf-8"))
    ok = True
    results = {}
    for qid, body in queries:
        try:
            results[qid] = pd.read_sql_query(to_sqlite(body), con)
            print(f"{qid:<4} OK   rows={len(results[qid])}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"{qid:<4} FAIL {exc}")
    print(f"\nExecuted {len(queries)} queries, {'all passed' if ok else 'FAILURES present'}")

    # ---- cross-check against pandas
    df = pd.read_csv(cfg.CLEAN_CSV)
    checks = {
        "Q1 total": (results["Q1"].iloc[0, 0], len(df)),
        "Q2 active": (results["Q2"].iloc[0, 0], int((df.Attrition == "No").sum())),
        "Q3 left": (results["Q3"].iloc[0, 0], int((df.Attrition == "Yes").sum())),
        "Q4 rate": (results["Q4"]["attrition_rate_pct"].iloc[0], round(100 * df.AttritionFlag.mean(), 2)),
        "Q6 top dept rate": (results["Q6"]["attrition_rate_pct"].iloc[0],
                             round(100 * df.groupby("Department").AttritionFlag.mean().max(), 2)),
        "Q7 top role rate": (results["Q7"]["attrition_rate_pct"].iloc[0],
                             round(100 * df.groupby("JobRole").AttritionFlag.mean().max(), 2)),
        "Q12 overtime=Yes rate": (
            float(results["Q12"].set_index("overtime").loc["Yes", "attrition_rate_pct"]),
            round(100 * df[df.OverTime == "Yes"].AttritionFlag.mean(), 2)),
        "Q14 >5yrs exp": (int(results["Q14"]["employees_over_5_yrs_experience"].sum()),
                          int((df.TotalWorkingYears > 5).sum())),
        "Q15 no promo 5+": (int(results["Q15"]["employees_no_promotion_5plus_yrs"].sum()),
                            int((df.YearsSinceLastPromotion >= 5).sum())),
        "Q17 lowest slab rate": (float(results["Q17"]["attrition_rate_pct"].iloc[0]),
                                 round(100 * df[df.MonthlyIncome < 3000].AttritionFlag.mean(), 2)),
    }
    for name, (sql_v, py_v) in checks.items():
        match = abs(float(sql_v) - float(py_v)) < 0.01
        ok &= match
        print(f"  check {name:<24} SQL={sql_v!s:<8} pandas={py_v!s:<8} {'PASS' if match else 'MISMATCH'}")

    # save every result for transparency
    out_dir = cfg.TABLES_DIR / "sql_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    for qid, res in results.items():
        res.to_csv(out_dir / f"{qid}.csv", index=False)
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
