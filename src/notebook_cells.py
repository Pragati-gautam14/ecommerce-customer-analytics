CELLS = [
("md", """# E-commerce Customer Analytics — Analysis Walkthrough
**Business question:** Who are our most valuable customers, how well do we retain them, and where should marketing spend go next?

**Data:** UCI Online Retail — 541,909 invoice lines from a UK online gift retailer (Dec 2010 – Dec 2011).
All transformations are written in **SQL** (`sql/` folder, run on DuckDB); Python is used for orchestration and visualisation."""),
("code", """import duckdb, pandas as pd, matplotlib.pyplot as plt
pd.set_option('display.max_columns', 20); pd.set_option('display.width', 160)
con = duckdb.connect('../data/retail.duckdb', read_only=True)
q = lambda s: con.sql(s).df()"""),
("md", "## 1. Data quality audit\nEvery cleaning rule is logged so the impact is transparent. Rows without a CustomerID can't be used for customer-level analysis; cancelled orders, postage/fee lines and purchases later reversed by a cancellation are removed."),
("code", "q('SELECT * FROM data_quality_log')"),
("md", "## 2. Headline KPIs and monthly trend\nMonth-over-month growth and cumulative revenue are computed with SQL window functions (`LAG`, running `SUM`)."),
("code", "display(q('SELECT * FROM headline_kpis'))\nq('SELECT * FROM monthly_kpis')"),
("md", "![monthly](../outputs/charts/01_monthly_revenue.png)\n\n**Insight:** revenue more than doubles from the Feb-2011 low to the Nov-2011 peak — Sep–Nov is the critical trading window (gift season). December 2011 only has 9 days of data, so it is excluded from trend conclusions."),
("md", "## 3. RFM segmentation\nCustomers are scored 1–5 on Recency, Frequency and Monetary value using `NTILE(5)`, then mapped to business segments."),
("code", "q('SELECT * FROM rfm_segment_summary')"),
("code", "q(\"SELECT customer_id, country, recency_days, frequency, monetary, rfm_code FROM rfm WHERE segment='At Risk (High Value)' ORDER BY monetary DESC LIMIT 10\")"),
("md", "![rfm](../outputs/charts/02_rfm_segments.png)\n\n**Insight:** ~22% of customers (Champions) generate ~67% of revenue. The *At Risk (High Value)* list above is a ready-made target list for a win-back campaign."),
("md", "## 4. Cohort retention"),
("code", "pv = q('SELECT * FROM cohort_retention WHERE cohort_month < DATE \\'2011-12-01\\'').pivot(index='cohort_month', columns='month_number', values='retention_pct')\npv.iloc[:, :8]"),
("code", "display(q('SELECT * FROM repeat_rate'))\nq('SELECT month_number, ROUND(AVG(retention_pct),1) AS avg_retention_pct FROM cohort_retention WHERE month_number BETWEEN 1 AND 6 GROUP BY 1 ORDER BY 1')"),
("md", "![cohort](../outputs/charts/03_cohort_retention.png)\n\n**Insight:** only ~20% of new customers come back the next month, but repeat customers produce >90% of revenue — improving early retention (welcome series, second-order discount) has the largest upside."),
("md", "## 5. Products, countries and cancellations"),
("code", "display(q('SELECT description, ROUND(revenue) revenue, units, buyers, cum_revenue_pct FROM product_pareto LIMIT 10'))\ndisplay(q('SELECT * FROM country_summary LIMIT 10'))\nq('SELECT * FROM cancellations_summary')"),
("md", "![pareto](../outputs/charts/04_product_pareto.png)\n![heatmap](../outputs/charts/05_weekday_hour_heatmap.png)"),
("md", "## 6. Market basket analysis (pure SQL)\nSelf-join on invoice to count product pairs; support, confidence and lift computed in SQL."),
("code", "q('SELECT * FROM basket_rules WHERE product_a < product_b ORDER BY baskets_together DESC LIMIT 15')"),
("md", """## 7. Recommendations
1. **Protect Champions** — loyalty tier / early access to Q4 ranges; they are ~67% of revenue.
2. **Win back At-Risk high-value customers** — targeted reactivation offer to the exported list.
3. **Fix first-90-day retention** — welcome journey + second-purchase incentive; month-1 retention is only ~20%.
4. **Plan for Q4** — Sep–Nov ≈ 38% of annual revenue; inventory and staffing should ramp from August.
5. **Bundle high-lift pairs** — 'frequently bought together' widgets for teacups, lunch bags, alarm clocks.
6. **Diversify beyond the UK** — 82% revenue concentration; Netherlands, EIRE, Germany and France already show high revenue per customer."""),
]
