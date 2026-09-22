-- ============================================================
-- 05_operations_analytics.sql
-- Operations, Delivery, Customer Experience & Geography
-- ============================================================


-- ============================================================
-- 1. OVERALL OPERATIONS PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE operations_summary AS

SELECT
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
    ) AS delivered_orders,

    COUNT(*) FILTER (
        WHERE is_canceled = TRUE
    ) AS canceled_orders,

    COUNT(*) FILTER (
        WHERE is_unavailable = TRUE
    ) AS unavailable_orders,

    ROUND(
        AVG(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS average_delivery_days,

    ROUND(
        MEDIAN(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS median_delivery_days,

    ROUND(
        AVG(estimated_delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS average_estimated_delivery_days,

    ROUND(
        AVG(delivery_delay_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS average_delivery_delay_days,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
          AND is_late = TRUE
    ) AS late_delivered_orders,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
          AND is_late = FALSE
    ) AS on_time_delivered_orders,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE is_delivered = TRUE
              AND is_late = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE is_delivered = TRUE
                  AND is_late IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_rate

FROM fact_orders;


-- ============================================================
-- 2. MONTHLY OPERATIONS PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE monthly_operations AS

SELECT
    order_purchase_year,
    order_purchase_month_num,
    order_purchase_month,

    COUNT(*) AS orders,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
    ) AS delivered_orders,

    ROUND(
        AVG(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS average_delivery_days,

    ROUND(
        AVG(delivery_delay_days) FILTER (
            WHERE is_delivered = TRUE
        ), 2
    ) AS average_delivery_delay_days,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
          AND is_late = TRUE
    ) AS late_orders,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE is_delivered = TRUE
              AND is_late = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE is_delivered = TRUE
                  AND is_late IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_rate

FROM fact_orders

GROUP BY
    order_purchase_year,
    order_purchase_month_num,
    order_purchase_month

ORDER BY
    order_purchase_year,
    order_purchase_month_num;


-- ============================================================
-- 3. CUSTOMER STATE OPERATIONS
-- ============================================================

CREATE OR REPLACE TABLE customer_state_operations AS

SELECT
    customer_state,

    COUNT(*) AS orders,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
    ) AS delivered_orders,

    ROUND(
        SUM(product_revenue) FILTER (
            WHERE has_items = TRUE
        ),
        2
    ) AS revenue,

    ROUND(
        AVG(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ),
        2
    ) AS average_delivery_days,

    ROUND(
        MEDIAN(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ),
        2
    ) AS median_delivery_days,

    ROUND(
        AVG(delivery_delay_days) FILTER (
            WHERE is_delivered = TRUE
        ),
        2
    ) AS average_delivery_delay_days,

    COUNT(*) FILTER (
        WHERE is_delivered = TRUE
          AND is_late = TRUE
    ) AS late_orders,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE is_delivered = TRUE
              AND is_late = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE is_delivered = TRUE
                  AND is_late IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_rate,

    ROUND(
        AVG(average_review_score) FILTER (
            WHERE average_review_score IS NOT NULL
        ),
        2
    ) AS average_review_score

FROM fact_orders

GROUP BY customer_state

ORDER BY revenue DESC;


-- ============================================================
-- 4. REVIEW & DELIVERY EXPERIENCE
-- ============================================================

CREATE OR REPLACE TABLE delivery_review_performance AS

SELECT
    CASE
        WHEN is_late = TRUE THEN 'Late'
        WHEN is_late = FALSE THEN 'On Time'
        ELSE 'Unknown'
    END AS delivery_status,

    COUNT(*) AS orders,

    COUNT(*) FILTER (
        WHERE average_review_score IS NOT NULL
    ) AS reviewed_orders,

    ROUND(
        AVG(average_review_score),
        2
    ) AS average_review_score,

    ROUND(
        AVG(delivery_days) FILTER (
            WHERE is_delivered = TRUE
        ),
        2
    ) AS average_delivery_days,

    ROUND(
        AVG(freight_ratio) FILTER (
            WHERE has_items = TRUE
        ),
        4
    ) AS average_freight_ratio

FROM fact_orders

GROUP BY delivery_status

ORDER BY
    CASE delivery_status
        WHEN 'Late' THEN 1
        WHEN 'On Time' THEN 2
        ELSE 3
    END;


-- ============================================================
-- 5. REVIEW SCORE DISTRIBUTION
-- ============================================================

CREATE OR REPLACE TABLE review_score_distribution AS

SELECT
    CAST(average_review_score AS INTEGER) AS review_score,

    COUNT(*) AS orders

FROM fact_orders

WHERE average_review_score IS NOT NULL

GROUP BY
    CAST(average_review_score AS INTEGER)

ORDER BY review_score;


-- ============================================================
-- 6. FREIGHT & CATEGORY OPERATIONS
-- ============================================================

CREATE OR REPLACE TABLE category_operations AS

SELECT
    product_category,

    COUNT(DISTINCT order_id) AS orders,

    COUNT(*) AS order_items,

    ROUND(SUM(item_revenue), 2) AS revenue,

    ROUND(SUM(item_freight), 2) AS freight,

    ROUND(
        SUM(item_freight)
        /
        NULLIF(SUM(item_revenue), 0),
        4
    ) AS freight_to_revenue_ratio,

    ROUND(
        AVG(freight_ratio),
        4
    ) AS average_item_freight_ratio,

    ROUND(
        AVG(item_total_value),
        2
    ) AS average_item_value

FROM fact_order_items

GROUP BY product_category

ORDER BY revenue DESC;


-- ============================================================
-- 7. SELLER DELIVERY PERFORMANCE
-- ============================================================

CREATE OR REPLACE TABLE seller_delivery_performance AS

SELECT
    foi.seller_id,

    MAX(foi.seller_city) AS seller_city,
    MAX(foi.seller_state) AS seller_state,

    COUNT(DISTINCT foi.order_id) AS orders,

    ROUND(
        SUM(foi.item_revenue),
        2
    ) AS revenue,

    ROUND(
        AVG(fo.delivery_days) FILTER (
            WHERE fo.is_delivered = TRUE
        ),
        2
    ) AS average_delivery_days,

    ROUND(
        AVG(fo.delivery_delay_days) FILTER (
            WHERE fo.is_delivered = TRUE
        ),
        2
    ) AS average_delivery_delay_days,

    COUNT(DISTINCT foi.order_id) FILTER (
        WHERE fo.is_delivered = TRUE
          AND fo.is_late = TRUE
    ) AS late_orders,

    ROUND(
        100.0 *
        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.is_delivered = TRUE
              AND fo.is_late = TRUE
        )
        /
        NULLIF(
            COUNT(DISTINCT foi.order_id) FILTER (
                WHERE fo.is_delivered = TRUE
                  AND fo.is_late IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_rate,

    ROUND(
        AVG(fo.average_review_score),
        2
    ) AS average_review_score

FROM fact_order_items foi

JOIN fact_orders fo
    ON foi.order_id = fo.order_id

GROUP BY
    foi.seller_id

ORDER BY revenue DESC;


-- ============================================================
-- 8. SELLER STATE OPERATIONS
-- ============================================================

CREATE OR REPLACE TABLE seller_state_operations AS

SELECT
    foi.seller_state,

    COUNT(DISTINCT foi.seller_id) AS sellers,

    COUNT(DISTINCT foi.order_id) AS orders,

    ROUND(
        SUM(foi.item_revenue),
        2
    ) AS revenue,

    ROUND(
        SUM(foi.item_freight),
        2
    ) AS freight,

    ROUND(
        AVG(fo.delivery_days) FILTER (
            WHERE fo.is_delivered = TRUE
        ),
        2
    ) AS average_delivery_days,

    COUNT(DISTINCT foi.order_id) FILTER (
        WHERE fo.is_delivered = TRUE
          AND fo.is_late = TRUE
    ) AS late_orders,

    ROUND(
        100.0 *
        COUNT(DISTINCT foi.order_id) FILTER (
            WHERE fo.is_delivered = TRUE
              AND fo.is_late = TRUE
        )
        /
        NULLIF(
            COUNT(DISTINCT foi.order_id) FILTER (
                WHERE fo.is_delivered = TRUE
                  AND fo.is_late IS NOT NULL
            ),
            0
        ),
        2
    ) AS late_delivery_rate

FROM fact_order_items foi

JOIN fact_orders fo
    ON foi.order_id = fo.order_id

GROUP BY foi.seller_state

ORDER BY revenue DESC;