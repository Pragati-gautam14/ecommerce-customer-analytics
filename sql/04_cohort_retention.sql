-- =============================================================
-- 04 · MONTHLY ACQUISITION-COHORT RETENTION
-- Cohort = month of first purchase; retention = % of cohort
-- that purchased again N months later
-- =============================================================
CREATE OR REPLACE TABLE cohort_retention AS
WITH first_order AS (
    SELECT customer_id, date_trunc('month', MIN(invoice_ts))::DATE AS cohort_month
    FROM sales GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT s.customer_id, f.cohort_month,
           date_trunc('month', s.invoice_ts)::DATE AS active_month
    FROM sales s JOIN first_order f USING (customer_id)
),
counts AS (
    SELECT cohort_month,
           date_diff('month', cohort_month, active_month) AS month_number,
           COUNT(DISTINCT customer_id)                    AS customers
    FROM activity GROUP BY ALL
)
SELECT c.cohort_month, c.month_number, c.customers,
       FIRST_VALUE(c.customers) OVER (PARTITION BY c.cohort_month ORDER BY c.month_number) AS cohort_size,
       ROUND(100.0 * c.customers /
             FIRST_VALUE(c.customers) OVER (PARTITION BY c.cohort_month ORDER BY c.month_number), 1) AS retention_pct
FROM counts c
ORDER BY cohort_month, month_number;

-- Repeat-purchase rate: share of customers with 2+ orders
CREATE OR REPLACE TABLE repeat_rate AS
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE frequency >= 2) / COUNT(*), 1) AS repeat_customer_pct,
       ROUND(100.0 * SUM(monetary) FILTER (WHERE frequency >= 2) / SUM(monetary), 1) AS repeat_revenue_pct
FROM rfm;
