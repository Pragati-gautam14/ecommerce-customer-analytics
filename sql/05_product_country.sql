-- =============================================================
-- 05 · PRODUCT PARETO, COUNTRY MIX & RETURNS
-- =============================================================
CREATE OR REPLACE TABLE product_pareto AS
WITH p AS (
    SELECT stock_code, ANY_VALUE(description) AS description,
           SUM(line_revenue) AS revenue, SUM(quantity) AS units,
           COUNT(DISTINCT customer_id) AS buyers
    FROM sales GROUP BY stock_code
)
SELECT *,
    ROW_NUMBER() OVER (ORDER BY revenue DESC)                                      AS revenue_rank,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(revenue) OVER (), 2) AS cum_revenue_pct,
    ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY revenue DESC) / COUNT(*) OVER (), 2)    AS cum_product_pct
FROM p
ORDER BY revenue DESC;

CREATE OR REPLACE TABLE country_summary AS
SELECT country,
       ROUND(SUM(line_revenue), 0)                                AS revenue,
       COUNT(DISTINCT customer_id)                                AS customers,
       COUNT(DISTINCT invoice_no)                                 AS orders,
       ROUND(SUM(line_revenue) / COUNT(DISTINCT invoice_no), 2)   AS avg_order_value,
       ROUND(SUM(line_revenue) / COUNT(DISTINCT customer_id), 0)  AS revenue_per_customer,
       ROUND(100.0 * SUM(line_revenue) / SUM(SUM(line_revenue)) OVER (), 2) AS pct_revenue
FROM sales GROUP BY country ORDER BY revenue DESC;

-- Cancellations: value lost & products most often cancelled
CREATE OR REPLACE TABLE cancellations_summary AS
SELECT
    ROUND(-SUM(line_revenue) FILTER (WHERE is_cancellation AND NOT is_non_product), 0) AS cancelled_value,
    ROUND(SUM(line_revenue) FILTER (WHERE NOT is_cancellation AND NOT is_non_product AND unit_price > 0), 0) AS gross_value,
    ROUND(100.0 * -SUM(line_revenue) FILTER (WHERE is_cancellation AND NOT is_non_product)
          / SUM(line_revenue) FILTER (WHERE NOT is_cancellation AND NOT is_non_product AND unit_price > 0), 2) AS cancel_rate_pct
FROM sales_lines WHERE customer_id IS NOT NULL;

CREATE OR REPLACE TABLE top_cancelled_products AS
SELECT stock_code, ANY_VALUE(description) AS description,
       COUNT(DISTINCT invoice_no) AS cancel_invoices,
       ROUND(-SUM(line_revenue), 0) AS cancelled_value
FROM sales_lines
WHERE is_cancellation AND NOT is_non_product AND customer_id IS NOT NULL
GROUP BY stock_code ORDER BY cancelled_value DESC LIMIT 15;
