-- ============================================================
-- 03_customer_rfm.sql
-- Customer RFM Analysis
-- ============================================================

-- Reference date is the last purchase date in the dataset.
-- This keeps the analysis reproducible.
CREATE OR REPLACE TABLE customer_rfm AS

WITH base AS (
    SELECT
        customer_unique_id,
        order_count AS frequency,
        first_order_date,
        last_order_date,
        total_product_revenue AS monetary,

        DATE_DIFF(
            'day',
            CAST(last_order_date AS DATE),
            DATE '2018-10-17'
        ) AS recency

    FROM dim_customers
),

scored AS (
    SELECT
        *,

        -- Lower recency is better.
        -- Tie-breaker makes NTILE deterministic.
        NTILE(5) OVER (
            ORDER BY recency DESC, customer_unique_id
        ) AS recency_score,

        -- Higher monetary value is better.
        NTILE(5) OVER (
            ORDER BY monetary, customer_unique_id
        ) AS monetary_score,

        -- Frequency is highly skewed:
        -- 96.9% of customers have exactly one order.
        CASE
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 2
            WHEN frequency = 3 THEN 3
            WHEN frequency = 4 THEN 4
            WHEN frequency >= 5 THEN 5
        END AS frequency_score

    FROM base
),

segmented AS (
    SELECT
        *,
        CONCAT(
            recency_score,
            frequency_score,
            monetary_score
        ) AS rfm_score,

        CASE
            WHEN recency_score >= 4
                 AND frequency_score >= 4
                 AND monetary_score >= 4
                THEN 'Champions'

            WHEN recency_score >= 4
                 AND frequency_score >= 2
                THEN 'Loyal Customers'

            WHEN recency_score >= 4
                 AND frequency_score = 1
                THEN 'Recent Customers'

            WHEN recency_score <= 2
                 AND monetary_score >= 4
                THEN 'At Risk High Value'

            WHEN recency_score <= 2
                 AND frequency_score >= 2
                THEN 'At Risk Repeat'

            WHEN recency_score <= 2
                THEN 'Hibernating'

            WHEN monetary_score >= 4
                THEN 'High Value'

            ELSE 'Other'
        END AS customer_segment

    FROM scored
)

SELECT
    customer_unique_id,
    recency,
    frequency,
    monetary,
    first_order_date,
    last_order_date,
    recency_score,
    frequency_score,
    monetary_score,
    rfm_score,
    customer_segment

FROM segmented;