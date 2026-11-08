-- =============================================================
-- 01 · DATA CLEANING
-- Raw: 541,909 invoice lines (UCI Online Retail, Dec-2010 → Dec-2011)
-- Output: sales_lines (all valid lines incl. cancellations)
--         sales       (clean, customer-attributed purchase lines)
-- =============================================================

CREATE OR REPLACE TABLE sales_lines AS
SELECT
    InvoiceNo                                        AS invoice_no,
    StockCode                                        AS stock_code,
    TRIM(UPPER(Description))                         AS description,
    Quantity                                         AS quantity,
    strptime(InvoiceDate, '%m/%d/%Y %H:%M')          AS invoice_ts,
    UnitPrice                                        AS unit_price,
    CustomerID                                       AS customer_id,
    Country                                          AS country,
    Quantity * UnitPrice                             AS line_revenue,
    InvoiceNo LIKE 'C%'                              AS is_cancellation,
    -- non-merchandise codes: postage, fees, manual adjustments, samples
    StockCode IN ('POST','DOT','M','D','C2','CRUK','PADS','S',
                  'BANK CHARGES','AMAZONFEE','B','m')
      OR StockCode LIKE 'gift_%'                     AS is_non_product
FROM raw_sales;

-- Data-quality audit: how many rows each rule removes
CREATE OR REPLACE TABLE data_quality_log AS
SELECT 'Raw rows'                                 AS check_name, COUNT(*) AS rows FROM sales_lines
UNION ALL SELECT 'Missing CustomerID',            COUNT(*) FROM sales_lines WHERE customer_id IS NULL
UNION ALL SELECT 'Cancellation lines (C-invoices)',COUNT(*) FROM sales_lines WHERE is_cancellation
UNION ALL SELECT 'Non-product codes (postage/fees)',COUNT(*) FROM sales_lines WHERE is_non_product
UNION ALL SELECT 'Zero / negative price',         COUNT(*) FROM sales_lines WHERE unit_price <= 0
UNION ALL SELECT 'Negative qty, not cancellation',COUNT(*) FROM sales_lines WHERE quantity <= 0 AND NOT is_cancellation
UNION ALL SELECT 'Exact duplicate lines',         COUNT(*) - COUNT(DISTINCT (invoice_no, stock_code, quantity, invoice_ts, unit_price, customer_id)) FROM sales_lines;

-- Purchases that were later fully reversed by a matching cancellation
-- (same customer + product + quantity). Keeping them would inflate revenue,
-- e.g. a single 80,995-unit order that was cancelled minutes later.
CREATE OR REPLACE TABLE reversed_purchases AS
SELECT DISTINCT p.invoice_no, p.stock_code, p.quantity
FROM sales_lines p
JOIN sales_lines c
  ON  c.is_cancellation
  AND c.customer_id = p.customer_id
  AND c.stock_code  = p.stock_code
  AND c.quantity    = -p.quantity
  AND c.invoice_ts >= p.invoice_ts
WHERE NOT p.is_cancellation;

INSERT INTO data_quality_log SELECT 'Purchases reversed by a cancellation', COUNT(*) FROM reversed_purchases;

-- Clean analytical fact table
CREATE OR REPLACE TABLE sales AS
SELECT DISTINCT s.*
FROM sales_lines s
ANTI JOIN reversed_purchases r
  ON r.invoice_no = s.invoice_no AND r.stock_code = s.stock_code AND r.quantity = s.quantity
WHERE customer_id IS NOT NULL
  AND NOT is_cancellation
  AND NOT is_non_product
  AND quantity  > 0
  AND unit_price > 0;

INSERT INTO data_quality_log SELECT 'Clean rows kept', COUNT(*) FROM sales;
