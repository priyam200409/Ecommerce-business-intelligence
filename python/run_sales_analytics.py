import duckdb


DB_PATH = "data/ecommerce.duckdb"


queries = {
    "Q1 - Total Product Revenue": """
        SELECT
            ROUND(SUM(item_revenue), 2) AS total_product_revenue
        FROM fact_order_items
    """,

    "Q2 - Total Orders": """
        SELECT
            COUNT(*) AS total_orders
        FROM fact_orders
    """,

    "Q3 - Unique Customers": """
        SELECT
            COUNT(*) AS unique_customers
        FROM dim_customers
    """,

    "Q4 - Average Order Value": """
        SELECT
            ROUND(
                SUM(product_revenue) / NULLIF(COUNT(*), 0),
                2
            ) AS average_order_value
        FROM agg_order_items
    """,

    "Q5 - Monthly Revenue": """
        SELECT
            DATE_TRUNC('month', fo.order_purchase_timestamp) AS month,
            ROUND(SUM(aoi.product_revenue), 2) AS monthly_revenue
        FROM fact_orders AS fo
        INNER JOIN agg_order_items AS aoi
            ON fo.order_id = aoi.order_id
        GROUP BY 1
        ORDER BY 1
    """,

    "Q6 - Monthly Order Volume": """
        SELECT
            DATE_TRUNC('month', order_purchase_timestamp) AS month,
            COUNT(*) AS monthly_orders
        FROM fact_orders
        GROUP BY 1
        ORDER BY 1
    """,

    "Q7 - Revenue by Product Category": """
        SELECT
            COALESCE(product_category, 'Unknown') AS category,
            ROUND(SUM(item_revenue), 2) AS category_revenue
        FROM fact_order_items
        GROUP BY 1
        ORDER BY category_revenue DESC
    """,

    "Q8 - Revenue by Customer State": """
        SELECT
            customer_state AS state,
            ROUND(SUM(product_revenue), 2) AS state_revenue
        FROM fact_orders
        WHERE has_items = TRUE
        GROUP BY 1
        ORDER BY state_revenue DESC
    """
}


def main():
    con = duckdb.connect(DB_PATH)

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("SALES ANALYTICS")
    print("=" * 70)

    for name, query in queries.items():
        print(f"\n{name}")
        print("-" * 70)

        result = con.execute(query).fetchdf()
        print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()