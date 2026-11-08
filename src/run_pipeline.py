"""
End-to-end pipeline: raw CSV -> DuckDB SQL models -> tables (CSV) -> Power BI exports.
Run from the project root:  python src/run_pipeline.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "online_retail.csv"
DB = ROOT / "data" / "retail.duckdb"
TABLES = ROOT / "outputs" / "tables"
PBI = ROOT / "powerbi"

EXPORT = [
    "data_quality_log", "headline_kpis", "monthly_kpis", "revenue_by_day_hour",
    "rfm_segment_summary", "cohort_retention", "repeat_rate", "country_summary",
    "cancellations_summary", "top_cancelled_products",
]


def main() -> None:
    if not RAW.exists():
        raise SystemExit("Raw data missing - run: python src/download_data.py")
    TABLES.mkdir(parents=True, exist_ok=True)
    PBI.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute(f"CREATE OR REPLACE TABLE raw_sales AS SELECT * FROM read_csv_auto('{RAW.as_posix()}')")

    for sql_file in sorted((ROOT / "sql").glob("*.sql")):
        print(f"running {sql_file.name}")
        con.execute(sql_file.read_text(encoding="utf-8"))

    for t in EXPORT:
        con.table(t).df().to_csv(TABLES / f"{t}.csv", index=False)
    con.sql("SELECT * FROM product_pareto LIMIT 50").df().to_csv(TABLES / "top_products.csv", index=False)
    con.sql("SELECT * FROM basket_rules LIMIT 50").df().to_csv(TABLES / "basket_rules_top50.csv", index=False)

    # ---- Power BI star schema (fact + dimensions) ----
    con.sql("""SELECT invoice_no, stock_code, customer_id, invoice_ts::DATE AS date_key,
                      quantity, unit_price, line_revenue FROM sales""").df().to_csv(PBI / "fact_sales.csv", index=False)
    con.sql("""SELECT customer_id, country, segment, recency_days, frequency, monetary,
                      r_score, f_score, m_score FROM rfm""").df().to_csv(PBI / "dim_customer.csv", index=False)
    con.sql("""SELECT stock_code, ANY_VALUE(description) AS description FROM sales
               GROUP BY 1""").df().to_csv(PBI / "dim_product.csv", index=False)
    con.sql("""SELECT d::DATE AS date_key, year(d) AS year, month(d) AS month,
                      monthname(d) AS month_name, quarter(d) AS quarter, dayname(d) AS weekday
               FROM range(DATE '2010-12-01', DATE '2012-01-01', INTERVAL 1 DAY) t(d)""").df().to_csv(PBI / "dim_date.csv", index=False)
    con.close()
    print("done ->", TABLES)


if __name__ == "__main__":
    main()
