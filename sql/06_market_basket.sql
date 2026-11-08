-- =============================================================
-- 06 · MARKET BASKET ANALYSIS (product affinity, pure SQL)
-- support    = share of baskets containing both A and B
-- confidence = P(B | A)
-- lift       = confidence / P(B)   (>1 → bought together more than chance)
-- Restricted to products in >= 1% of baskets to keep it meaningful
-- =============================================================
CREATE OR REPLACE TABLE basket_rules AS
WITH baskets AS (SELECT DISTINCT invoice_no, stock_code FROM sales),
n AS (SELECT COUNT(DISTINCT invoice_no) AS total FROM baskets),
item AS (
    SELECT stock_code, COUNT(*) AS cnt FROM baskets GROUP BY stock_code
    HAVING COUNT(*) >= 0.01 * (SELECT total FROM n)
),
pairs AS (
    SELECT a.stock_code AS item_a, b.stock_code AS item_b, COUNT(*) AS pair_cnt
    FROM baskets a
    JOIN baskets b ON a.invoice_no = b.invoice_no AND a.stock_code <> b.stock_code
    WHERE a.stock_code IN (SELECT stock_code FROM item)
      AND b.stock_code IN (SELECT stock_code FROM item)
    GROUP BY 1, 2
),
names AS (SELECT stock_code, ANY_VALUE(description) AS description FROM sales GROUP BY 1)
SELECT
    na.description AS product_a, nb.description AS product_b,
    p.pair_cnt                                               AS baskets_together,
    ROUND(100.0 * p.pair_cnt / n.total, 2)                   AS support_pct,
    ROUND(100.0 * p.pair_cnt / ia.cnt, 1)                    AS confidence_pct,
    ROUND((p.pair_cnt * 1.0 / ia.cnt) / (ib.cnt * 1.0 / n.total), 2) AS lift
FROM pairs p
JOIN item ia ON ia.stock_code = p.item_a
JOIN item ib ON ib.stock_code = p.item_b
JOIN names na ON na.stock_code = p.item_a
JOIN names nb ON nb.stock_code = p.item_b
CROSS JOIN n
WHERE p.pair_cnt >= 100
ORDER BY lift DESC, baskets_together DESC;
