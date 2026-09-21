-- ============================================================
-- E-COMMERCE BUSINESS INTELLIGENCE
-- SALES ANALYTICS
-- ============================================================


-- ============================================================
-- Q1: TOTAL PRODUCT REVENUE
-- ============================================================

SELECT
    ROUND(SUM(item_revenue), 2) AS total_product_revenue
FROM fact_order_items;


-- ============================================================
-- Q2: TOTAL ORDERS
-- ============================================================

SELECT
    COUNT(*) AS total_orders
FROM fact_orders;


-- ============================================================
-- Q3: UNIQUE CUSTOMERS
-- ============================================================

SELECT
    COUNT(*) AS unique_customers
FROM dim_customers;


-- ============================================================
-- Q4: AVERAGE ORDER VALUE
-- ============================================================

SELECT
    ROUND(
        SUM(product_revenue) / NULLIF(COUNT(*), 0),
        2
    ) AS average_order_value
FROM agg_order_items;


-- ============================================================
-- Q5: MONTHLY REVENUE
-- ============================================================

SELECT
    DATE_TRUNC('month', fo.order_purchase_timestamp) AS month,
    ROUND(SUM(aoi.product_revenue), 2) AS monthly_revenue
FROM fact_orders AS fo
INNER JOIN agg_order_items AS aoi
    ON fo.order_id = aoi.order_id
GROUP BY 1
ORDER BY 1;


-- ============================================================
-- Q6: MONTHLY ORDER VOLUME
-- ============================================================

SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS month,
    COUNT(*) AS monthly_orders
FROM fact_orders
GROUP BY 1
ORDER BY 1;


-- ============================================================
-- Q7: REVENUE BY PRODUCT CATEGORY
-- ============================================================

SELECT
    COALESCE(product_category, 'Unknown') AS category,
    ROUND(SUM(item_revenue), 2) AS category_revenue
FROM fact_order_items
GROUP BY 1
ORDER BY category_revenue DESC;


-- ============================================================
-- Q8: REVENUE BY CUSTOMER STATE
-- ============================================================

SELECT
    customer_state AS state,
    ROUND(SUM(product_revenue), 2) AS state_revenue
FROM fact_orders
WHERE has_items = TRUE
GROUP BY 1
ORDER BY state_revenue DESC;