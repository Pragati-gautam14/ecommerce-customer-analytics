-- =============================================================
-- 03 · RFM CUSTOMER SEGMENTATION
-- Recency  = days since last purchase (snapshot = day after last invoice)
-- Frequency= distinct invoices, Monetary = total spend
-- Scores 1-5 via NTILE; segments via standard RFM rules
-- =============================================================
CREATE OR REPLACE TABLE rfm AS
WITH snapshot AS (SELECT MAX(invoice_ts)::DATE + 1 AS snap FROM sales),
base AS (
    SELECT
        customer_id,
        ANY_VALUE(country)                                    AS country,
        date_diff('day', MAX(invoice_ts)::DATE, (SELECT snap FROM snapshot)) AS recency_days,
        COUNT(DISTINCT invoice_no)                            AS frequency,
        ROUND(SUM(line_revenue), 2)                           AS monetary,
        MIN(invoice_ts)::DATE                                 AS first_purchase,
        MAX(invoice_ts)::DATE                                 AS last_purchase
    FROM sales
    GROUP BY customer_id
),
scored AS (
    SELECT *,
        6 - NTILE(5) OVER (ORDER BY recency_days, customer_id) AS r_score,   -- recent = 5 (customer_id breaks ties)
        NTILE(5) OVER (ORDER BY frequency, customer_id)      AS f_score,
        NTILE(5) OVER (ORDER BY monetary, customer_id)       AS m_score
    FROM base
)
SELECT *,
    r_score::VARCHAR || f_score::VARCHAR || m_score::VARCHAR  AS rfm_code,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                   THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                   THEN 'New / Promising'
        WHEN r_score  = 3 AND f_score <= 2                   THEN 'Need Attention'
        WHEN r_score <= 2 AND f_score >= 4                   THEN 'At Risk (High Value)'
        WHEN r_score <= 2 AND f_score  = 3                   THEN 'About to Sleep'
        ELSE 'Hibernating / Lost'
    END AS segment
FROM scored;

CREATE OR REPLACE TABLE rfm_segment_summary AS
SELECT
    segment,
    COUNT(*)                                                       AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_customers,
    ROUND(SUM(monetary), 0)                                        AS revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1)   AS pct_revenue,
    ROUND(AVG(recency_days), 0)                                    AS avg_recency_days,
    ROUND(AVG(frequency), 1)                                       AS avg_orders,
    ROUND(AVG(monetary), 0)                                        AS avg_spend
FROM rfm
GROUP BY segment
ORDER BY revenue DESC;
