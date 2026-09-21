-- ============================================================
-- E-COMMERCE BUSINESS INTELLIGENCE
-- DUCKDB DATABASE SETUP
-- ============================================================

-- Create a local analytical database.
-- The database file itself should remain local and is ignored
-- by Git.

CREATE OR REPLACE TABLE fact_order_items AS
SELECT *
FROM read_csv_auto(
    'data/processed/fact_order_items.csv',
    HEADER = TRUE
);

CREATE OR REPLACE TABLE agg_order_items AS
SELECT *
FROM read_csv_auto(
    'data/processed/agg_order_items.csv',
    HEADER = TRUE
);

CREATE OR REPLACE TABLE agg_order_payments AS
SELECT *
FROM read_csv_auto(
    'data/processed/agg_order_payments.csv',
    HEADER = TRUE
);

CREATE OR REPLACE TABLE agg_order_reviews AS
SELECT *
FROM read_csv_auto(
    'data/processed/agg_order_reviews.csv',
    HEADER = TRUE
);

CREATE OR REPLACE TABLE fact_orders AS
SELECT *
FROM read_csv_auto(
    'data/processed/fact_orders.csv',
    HEADER = TRUE
);

CREATE OR REPLACE TABLE dim_customers AS
SELECT *
FROM read_csv_auto(
    'data/processed/dim_customers.csv',
    HEADER = TRUE
);


-- ============================================================
-- BASIC TABLE CHECK
-- ============================================================

SELECT
    'fact_order_items' AS table_name,
    COUNT(*) AS row_count
FROM fact_order_items

UNION ALL

SELECT
    'agg_order_items',
    COUNT(*)
FROM agg_order_items

UNION ALL

SELECT
    'agg_order_payments',
    COUNT(*)
FROM agg_order_payments

UNION ALL

SELECT
    'agg_order_reviews',
    COUNT(*)
FROM agg_order_reviews

UNION ALL

SELECT
    'fact_orders',
    COUNT(*)
FROM fact_orders

UNION ALL

SELECT
    'dim_customers',
    COUNT(*)
FROM dim_customers;