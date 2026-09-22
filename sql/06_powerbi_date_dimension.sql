-- ============================================================
-- 06_powerbi_date_dimension.sql
-- Power BI Date Dimension
-- ============================================================

CREATE OR REPLACE TABLE dim_date AS

WITH date_range AS (
    SELECT
        MIN(order_purchase_date) AS min_date,
        MAX(order_purchase_date) AS max_date
    FROM fact_orders
),

dates AS (
    SELECT
        UNNEST(
            GENERATE_SERIES(
                min_date,
                max_date,
                INTERVAL 1 DAY
            )
        )::DATE AS date_day
    FROM date_range
)

SELECT
    date_day AS date,

    EXTRACT(YEAR FROM date_day)::INTEGER AS year,

    EXTRACT(QUARTER FROM date_day)::INTEGER AS quarter,

    EXTRACT(MONTH FROM date_day)::INTEGER AS month_number,

    STRFTIME(date_day, '%B') AS month_name,

    STRFTIME(date_day, '%Y-%m') AS year_month,

    EXTRACT(WEEK FROM date_day)::INTEGER AS week_number,

    EXTRACT(DAY FROM date_day)::INTEGER AS day_of_month,

    STRFTIME(date_day, '%A') AS day_name,

    EXTRACT(DOW FROM date_day)::INTEGER AS day_of_week,

    CASE
        WHEN EXTRACT(DOW FROM date_day) IN (0, 6)
        THEN TRUE
        ELSE FALSE
    END AS is_weekend

FROM dates

ORDER BY date;