import duckdb
import pandas as pd


DB_PATH = "data/ecommerce.duckdb"
REPORT_PATH = "reports/sales_analytics_validation.csv"


def main():
    con = duckdb.connect(DB_PATH)

    checks = []

    # ---------------------------------------------------------
    # 1. Total product revenue
    # ---------------------------------------------------------

    detail_revenue = con.execute("""
        SELECT ROUND(SUM(item_revenue), 2)
        FROM fact_order_items
    """).fetchone()[0]

    analytical_revenue = con.execute("""
        SELECT ROUND(SUM(product_revenue), 2)
        FROM agg_order_items
    """).fetchone()[0]

    checks.append({
        "check": "Product revenue reconciliation",
        "status": "PASS" if detail_revenue == analytical_revenue else "FAIL",
        "detail": f"Detail={detail_revenue}; Aggregated={analytical_revenue}"
    })

    # ---------------------------------------------------------
    # 2. Total orders
    # ---------------------------------------------------------

    fact_orders = con.execute("""
        SELECT COUNT(*)
        FROM fact_orders
    """).fetchone()[0]

    expected_orders = 99441

    checks.append({
        "check": "Total order count",
        "status": "PASS" if fact_orders == expected_orders else "FAIL",
        "detail": f"Expected={expected_orders}; Actual={fact_orders}"
    })

    # ---------------------------------------------------------
    # 3. Unique customers
    # ---------------------------------------------------------

    unique_customers = con.execute("""
        SELECT COUNT(*)
        FROM dim_customers
    """).fetchone()[0]

    expected_customers = 96096

    checks.append({
        "check": "Unique customer count",
        "status": "PASS" if unique_customers == expected_customers else "FAIL",
        "detail": f"Expected={expected_customers}; Actual={unique_customers}"
    })

    # ---------------------------------------------------------
    # 4. Orders with items
    # ---------------------------------------------------------

    orders_with_items = con.execute("""
        SELECT COUNT(*)
        FROM agg_order_items
    """).fetchone()[0]

    expected_orders_with_items = con.execute("""
        SELECT COUNT(*)
        FROM fact_orders
        WHERE has_items = TRUE
    """).fetchone()[0]

    checks.append({
        "check": "Orders with items reconciliation",
        "status": (
            "PASS"
            if orders_with_items == expected_orders_with_items
            else "FAIL"
        ),
        "detail": (
            f"Aggregated={orders_with_items}; "
            f"Fact orders={expected_orders_with_items}"
        )
    })

    # ---------------------------------------------------------
    # 5. Category revenue reconciliation
    # ---------------------------------------------------------

    category_revenue = con.execute("""
        SELECT ROUND(SUM(item_revenue), 2)
        FROM fact_order_items
    """).fetchone()[0]

    checks.append({
        "check": "Category revenue reconciliation",
        "status": "PASS" if category_revenue == detail_revenue else "FAIL",
        "detail": f"Category total={category_revenue}; Revenue={detail_revenue}"
    })

    # ---------------------------------------------------------
    # 6. State revenue reconciliation
    # ---------------------------------------------------------

    state_revenue = con.execute("""
        SELECT ROUND(SUM(product_revenue), 2)
        FROM fact_orders
        WHERE has_items = TRUE
    """).fetchone()[0]

    checks.append({
        "check": "State revenue reconciliation",
        "status": "PASS" if state_revenue == detail_revenue else "FAIL",
        "detail": f"State total={state_revenue}; Revenue={detail_revenue}"
    })

    # ---------------------------------------------------------
    # 7. Monthly revenue reconciliation
    # ---------------------------------------------------------

    monthly_revenue = con.execute("""
        SELECT ROUND(SUM(monthly_revenue), 2)
        FROM (
            SELECT
                DATE_TRUNC('month', fo.order_purchase_timestamp) AS month,
                SUM(aoi.product_revenue) AS monthly_revenue
            FROM fact_orders fo
            INNER JOIN agg_order_items aoi
                ON fo.order_id = aoi.order_id
            GROUP BY 1
        )
    """).fetchone()[0]

    checks.append({
        "check": "Monthly revenue reconciliation",
        "status": "PASS" if monthly_revenue == detail_revenue else "FAIL",
        "detail": f"Monthly total={monthly_revenue}; Revenue={detail_revenue}"
    })

    # ---------------------------------------------------------
    # 8. Monthly order reconciliation
    # ---------------------------------------------------------

    monthly_orders = con.execute("""
        SELECT SUM(monthly_orders)
        FROM (
            SELECT
                DATE_TRUNC('month', order_purchase_timestamp) AS month,
                COUNT(*) AS monthly_orders
            FROM fact_orders
            GROUP BY 1
        )
    """).fetchone()[0]

    checks.append({
        "check": "Monthly order reconciliation",
        "status": (
            "PASS"
            if monthly_orders == fact_orders
            else "FAIL"
        ),
        "detail": f"Monthly total={monthly_orders}; Orders={fact_orders}"
    })

    # ---------------------------------------------------------
    # Save report
    # ---------------------------------------------------------

    report = pd.DataFrame(checks)
    report.to_csv(REPORT_PATH, index=False)

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("SALES ANALYTICS VALIDATION")
    print("=" * 70)

    print(report.to_string(index=False))

    print("\nValidation Summary:")
    print(report["status"].value_counts())

    if (report["status"] == "FAIL").any():
        raise SystemExit("Sales analytics validation failed.")

    print("\nSALES ANALYTICS VALIDATION COMPLETED")
    print("All validation checks passed.")

    con.close()


if __name__ == "__main__":
    main()