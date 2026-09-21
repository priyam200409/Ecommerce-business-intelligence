-- ============================================================
-- 04_product_seller_analytics.sql
-- Product & Seller Intelligence
-- ============================================================


-- ============================================================
-- 1. PRODUCT CATEGORY PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE category_performance AS

SELECT
    product_category,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS order_items,
    COUNT(DISTINCT product_id) AS unique_products,
    ROUND(SUM(item_revenue), 2) AS revenue,
    ROUND(SUM(item_freight), 2) AS freight,
    ROUND(SUM(item_total_value), 2) AS total_value,
    ROUND(AVG(price), 2) AS average_item_price,
    ROUND(AVG(item_total_value), 2) AS average_item_value,
    ROUND(AVG(freight_ratio), 4) AS average_freight_ratio

FROM fact_order_items

GROUP BY product_category

ORDER BY revenue DESC;


-- ============================================================
-- 2. PRODUCT PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE product_performance AS

SELECT
    product_id,
    product_category,
    product_category_name_english,

    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS order_items,

    COUNT(DISTINCT seller_id) AS sellers,

    ROUND(SUM(item_revenue), 2) AS revenue,
    ROUND(SUM(item_freight), 2) AS freight,
    ROUND(SUM(item_total_value), 2) AS total_value,

    ROUND(AVG(price), 2) AS average_price,
    ROUND(AVG(item_total_value), 2) AS average_item_value,
    ROUND(AVG(freight_ratio), 4) AS average_freight_ratio

FROM fact_order_items

GROUP BY
    product_id,
    product_category,
    product_category_name_english

ORDER BY revenue DESC;


-- ============================================================
-- 3. SELLER PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE seller_performance AS

SELECT
    seller_id,

    seller_city,
    seller_state,

    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS order_items,
    COUNT(DISTINCT product_id) AS unique_products,

    ROUND(SUM(item_revenue), 2) AS revenue,
    ROUND(SUM(item_freight), 2) AS freight,
    ROUND(SUM(item_total_value), 2) AS total_value,

    ROUND(AVG(price), 2) AS average_item_price,
    ROUND(AVG(item_total_value), 2) AS average_item_value,
    ROUND(AVG(freight_ratio), 4) AS average_freight_ratio

FROM fact_order_items

GROUP BY
    seller_id,
    seller_city,
    seller_state

ORDER BY revenue DESC;


-- ============================================================
-- 4. SELLER CATEGORY COVERAGE
-- ============================================================

CREATE OR REPLACE TABLE seller_category_performance AS

SELECT
    seller_id,
    seller_state,
    product_category,

    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS order_items,

    ROUND(SUM(item_revenue), 2) AS revenue,
    ROUND(SUM(item_freight), 2) AS freight,

    ROUND(AVG(price), 2) AS average_item_price

FROM fact_order_items

GROUP BY
    seller_id,
    seller_state,
    product_category

ORDER BY revenue DESC;


-- ============================================================
-- 5. SELLER STATE PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE seller_state_performance AS

SELECT
    seller_state,

    COUNT(DISTINCT seller_id) AS sellers,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(*) AS order_items,

    ROUND(SUM(item_revenue), 2) AS revenue,
    ROUND(SUM(item_freight), 2) AS freight,
    ROUND(SUM(item_total_value), 2) AS total_value,

    ROUND(AVG(item_total_value), 2) AS average_item_value,
    ROUND(AVG(freight_ratio), 4) AS average_freight_ratio

FROM fact_order_items

GROUP BY seller_state

ORDER BY revenue DESC;