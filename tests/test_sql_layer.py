"""Execute the T-SQL scripts against DuckDB and compare with the Python layer.

The SQL is written for SQL Server. sqlglot translates each batch to DuckDB so
the SAME view definitions can be tested in CI without a SQL Server instance.
Only two T-SQL features need help: CONVERT style 103 dates and recursive CTEs.
"""

import re
from pathlib import Path

import pytest

duckdb = pytest.importorskip("duckdb")
sqlglot = pytest.importorskip("sqlglot")

from autosales import kpis  # noqa: E402
from autosales.config import RAW_CSV, REPO_ROOT  # noqa: E402

SQL_DIR = REPO_ROOT / "sql"
SKIP_PREFIXES = ("USE ", "IF ", "DROP TABLE", "CREATE TABLE", "DECLARE", "INSERT", "UPDATE",
                 "SELECT COUNT(*) AS BRONZE", "EXEC")


def _batches(path: Path):
    text = path.read_text(encoding="utf-8")
    for b in re.split(r"^\s*GO\s*$", text, flags=re.M):
        body = re.sub(r"/\*.*?\*/", "", b, flags=re.S).strip()
        if body:
            yield body


def _to_duckdb(body: str):
    body = body.replace("CREATE OR ALTER VIEW", "CREATE OR REPLACE VIEW")
    body = re.sub(r"TRY_CONVERT\(DATE,\s*(.+?), 103\)", r"TRY_STRPTIME(\1, '%d/%m/%Y')::DATE", body)
    for stmt in sqlglot.transpile(body, read="tsql", write="duckdb"):
        yield stmt.replace("WITH bounds AS", "WITH RECURSIVE bounds AS")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    for s in ("bronze", "silver", "gold"):
        c.execute(f"CREATE SCHEMA {s}")
    c.execute(f"CREATE TABLE bronze.auto_sales_raw AS SELECT * FROM read_csv('{RAW_CSV.as_posix()}', all_varchar=true, header=true)")
    for name in ("02_silver_transform.sql", "03_gold_model.sql"):
        for body in _batches(SQL_DIR / name):
            if body.upper().startswith(SKIP_PREFIXES) or body.upper().startswith("SELECT"):
                continue
            for stmt in _to_duckdb(body):
                c.execute(stmt)
    return c


def test_every_sql_batch_parses_as_tsql():
    for f in sorted(SQL_DIR.glob("*.sql")):
        for body in _batches(f):
            sqlglot.parse(body, read="tsql")


def test_data_quality_suite_passes(con):
    body = list(_batches(SQL_DIR / "05_data_quality_tests.sql"))[-1]
    df = con.execute(next(_to_duckdb(body))).fetchdf()
    failed = df[df["failures"] != 0]
    assert len(df) >= 20
    assert failed.empty, failed.to_string()


def test_sql_headline_matches_python(con, orders):
    sql = con.execute("SELECT * FROM gold.kpi_headline").fetchdf().iloc[0]
    py = kpis.headline(orders)
    for k in ("total_orders", "failed_orders", "open_orders", "at_risk_orders", "lost_orders"):
        assert int(sql[k]) == py[k], k
    for k in ("total_revenue", "revenue_at_risk", "revenue_lost", "open_pipeline_revenue"):
        assert float(sql[k]) == pytest.approx(py[k], abs=0.01), k
    for k in ("fulfilment_rate", "failure_rate", "issue_rate"):
        assert float(sql[k]) == pytest.approx(py[k], abs=1e-4), k


def test_sql_country_matches_python(con, orders):
    sql = con.execute("SELECT country, total_orders, total_revenue, failure_rate FROM gold.kpi_country").fetchdf()
    py = kpis.by_country(orders)
    m = sql.merge(py, on="country", suffixes=("_sql", "_py"))
    assert len(m) == 19
    assert (m["total_orders_sql"] == m["total_orders_py"]).all()
    assert (m["total_revenue_sql"].astype(float) - m["total_revenue_py"]).abs().max() < 0.01


def test_sql_product_lines_match_python(con, lines):
    sql = con.execute("SELECT product_line, SUM(revenue) AS revenue FROM gold.kpi_product_line_monthly GROUP BY 1").fetchdf()
    py = lines.groupby("product_line")["sales"].sum()
    for _, r in sql.iterrows():
        assert float(r["revenue"]) == pytest.approx(py[r["product_line"]], abs=0.01)
