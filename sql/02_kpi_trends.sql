-- =============================================================
-- 02 · MONTHLY KPI TRENDS (window functions)
-- Note: Dec-2011 contains only 9 days of data → flagged as partial
-- =============================================================
CREATE OR REPLACE TABLE monthly_kpis AS
WITH m AS (
    SELECT
        date_trunc('month', invoice_ts)::DATE        AS month,
        SUM(line_revenue)                            AS revenue,
        COUNT(DISTINCT invoice_no)                   AS orders,
        COUNT(DISTINCT customer_id)                  AS active_customers,
        SUM(quantity)                                AS units
    FROM sales
    GROUP BY 1
)
SELECT
    month,
    ROUND(revenue, 2)                                              AS revenue,
    orders,
    active_customers,
    units,
    ROUND(revenue / orders, 2)                                     AS avg_order_value,
    ROUND(100.0 * (revenue - LAG(revenue) OVER w) / LAG(revenue) OVER w, 1) AS mom_growth_pct,
    ROUND(SUM(revenue) OVER (ORDER BY month), 2)                   AS cumulative_revenue,
    month = DATE '2011-12-01'                                      AS is_partial_month
FROM m
WINDOW w AS (ORDER BY month)
ORDER BY month;

-- Headline KPIs for the full period
CREATE OR REPLACE TABLE headline_kpis AS
SELECT
    ROUND(SUM(line_revenue), 0)                                    AS total_revenue,
    COUNT(DISTINCT invoice_no)                                     AS total_orders,
    COUNT(DISTINCT customer_id)                                    AS total_customers,
    COUNT(DISTINCT stock_code)                                     AS total_products,
    COUNT(DISTINCT country)                                        AS countries,
    ROUND(SUM(line_revenue) / COUNT(DISTINCT invoice_no), 2)       AS avg_order_value,
    ROUND(COUNT(DISTINCT invoice_no) * 1.0 / COUNT(DISTINCT customer_id), 2) AS orders_per_customer
FROM sales;

-- Revenue by weekday × hour (for staffing / campaign timing)
CREATE OR REPLACE TABLE revenue_by_day_hour AS
SELECT
    dayname(invoice_ts)                 AS weekday,
    isodow(invoice_ts)                  AS weekday_num,
    hour(invoice_ts)                    AS hour,
    ROUND(SUM(line_revenue), 0)         AS revenue,
    COUNT(DISTINCT invoice_no)          AS orders
FROM sales
GROUP BY ALL
ORDER BY weekday_num, hour;
