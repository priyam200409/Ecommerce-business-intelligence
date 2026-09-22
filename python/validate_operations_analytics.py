from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"


def check(name, condition, details=""):
    status = "PASS" if condition else "FAIL"

    print(f"[{status}] {name}")

    if details:
        print(f"       {details}")

    return condition


def main():
    print("=" * 70)
    print("OPERATIONS ANALYTICS VALIDATION")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    results = []

    expected_tables = [
        "operations_summary",
        "monthly_operations",
        "customer_state_operations",
        "delivery_review_performance",
        "review_score_distribution",
        "category_operations",
        "seller_delivery_performance",
        "seller_state_operations",
    ]

    tables = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchdf()["table_name"].tolist()

    # ------------------------------------------------------------
    # 1. Required tables
    # ------------------------------------------------------------

    for table in expected_tables:
        results.append(
            check(
                f"{table} exists",
                table in tables
            )
        )

    # ------------------------------------------------------------
    # 2. Operations order count
    # ------------------------------------------------------------

    source_orders = conn.execute(
        "SELECT COUNT(*) FROM fact_orders"
    ).fetchone()[0]

    summary_orders = conn.execute(
        "SELECT total_orders FROM operations_summary"
    ).fetchone()[0]

    results.append(
        check(
            "Operations total orders reconciles",
            source_orders == summary_orders,
            f"source={source_orders:,}, summary={summary_orders:,}"
        )
    )

    # ------------------------------------------------------------
    # 3. Delivered orders
    # ------------------------------------------------------------

    source_delivered = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_orders
        WHERE is_delivered = TRUE
        """
    ).fetchone()[0]

    summary_delivered = conn.execute(
        "SELECT delivered_orders FROM operations_summary"
    ).fetchone()[0]

    results.append(
        check(
            "Delivered orders reconcile",
            source_delivered == summary_delivered,
            f"source={source_delivered:,}, summary={summary_delivered:,}"
        )
    )

    # ------------------------------------------------------------
    # 4. Late orders
    # ------------------------------------------------------------

    source_late = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_orders
        WHERE is_delivered = TRUE
          AND is_late = TRUE
        """
    ).fetchone()[0]

    summary_late = conn.execute(
        "SELECT late_delivered_orders FROM operations_summary"
    ).fetchone()[0]

    results.append(
        check(
            "Late delivered orders reconcile",
            source_late == summary_late,
            f"source={source_late:,}, summary={summary_late:,}"
        )
    )

    # ------------------------------------------------------------
    # 5. Monthly delivered orders
    # ------------------------------------------------------------

    monthly_delivered = conn.execute(
        """
        SELECT SUM(delivered_orders)
        FROM monthly_operations
        """
    ).fetchone()[0]

    results.append(
        check(
            "Monthly delivered orders reconcile",
            monthly_delivered == source_delivered,
            f"monthly={monthly_delivered:,}, source={source_delivered:,}"
        )
    )

    # ------------------------------------------------------------
    # 6. Customer state orders
    # ------------------------------------------------------------

    state_orders = conn.execute(
        """
        SELECT SUM(orders)
        FROM customer_state_operations
        """
    ).fetchone()[0]

    results.append(
        check(
            "Customer-state orders reconcile",
            state_orders == source_orders,
            f"state={state_orders:,}, source={source_orders:,}"
        )
    )

    # ------------------------------------------------------------
    # 7. Category revenue
    # ------------------------------------------------------------

    source_revenue = conn.execute(
        """
        SELECT SUM(item_revenue)
        FROM fact_order_items
        """
    ).fetchone()[0]

    category_revenue = conn.execute(
        """
        SELECT SUM(revenue)
        FROM category_operations
        """
    ).fetchone()[0]

    results.append(
        check(
            "Category operations revenue reconciles",
            abs(source_revenue - category_revenue) < 0.01,
            f"difference={abs(source_revenue - category_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 8. Category freight
    # ------------------------------------------------------------

    source_freight = conn.execute(
        """
        SELECT SUM(item_freight)
        FROM fact_order_items
        """
    ).fetchone()[0]

    category_freight = conn.execute(
        """
        SELECT SUM(freight)
        FROM category_operations
        """
    ).fetchone()[0]

    results.append(
        check(
            "Category operations freight reconciles",
            abs(source_freight - category_freight) < 0.01,
            f"difference={abs(source_freight - category_freight):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 9. Seller delivery revenue
    # ------------------------------------------------------------

    seller_revenue = conn.execute(
        """
        SELECT SUM(revenue)
        FROM seller_delivery_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller delivery revenue reconciles",
            abs(source_revenue - seller_revenue) < 0.01,
            f"difference={abs(source_revenue - seller_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 10. Seller-state revenue
    # ------------------------------------------------------------

    seller_state_revenue = conn.execute(
        """
        SELECT SUM(revenue)
        FROM seller_state_operations
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller-state revenue reconciles",
            abs(source_revenue - seller_state_revenue) < 0.01,
            f"difference={abs(source_revenue - seller_state_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 11. Review score validity
    # ------------------------------------------------------------

    invalid_review_scores = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_orders
        WHERE average_review_score IS NOT NULL
          AND (
              average_review_score < 1
              OR average_review_score > 5
          )
        """
    ).fetchone()[0]

    results.append(
        check(
            "Review scores remain within 1-5",
            invalid_review_scores == 0,
            f"invalid rows={invalid_review_scores:,}"
        )
    )

    # ------------------------------------------------------------
    # 12. Review distribution reconciliation
    # ------------------------------------------------------------

    reviewed_orders = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_orders
        WHERE average_review_score IS NOT NULL
        """
    ).fetchone()[0]

    distribution_orders = conn.execute(
        """
        SELECT SUM(orders)
        FROM review_score_distribution
        """
    ).fetchone()[0]

    results.append(
        check(
            "Review score distribution reconciles",
            reviewed_orders == distribution_orders,
            f"distribution={distribution_orders:,}, source={reviewed_orders:,}"
        )
    )

    # ------------------------------------------------------------
    # 13. Late delivery rate validity
    # ------------------------------------------------------------

    invalid_late_rates = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_state_operations
        WHERE late_delivery_rate < 0
           OR late_delivery_rate > 100
        """
    ).fetchone()[0]

    results.append(
        check(
            "Customer-state late rates are valid",
            invalid_late_rates == 0,
            f"invalid rows={invalid_late_rates:,}"
        )
    )

    # ------------------------------------------------------------
    # 14. Seller delivery rate validity
    # ------------------------------------------------------------

    invalid_seller_rates = conn.execute(
        """
        SELECT COUNT(*)
        FROM seller_delivery_performance
        WHERE late_delivery_rate < 0
           OR late_delivery_rate > 100
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller late rates are valid",
            invalid_seller_rates == 0,
            f"invalid rows={invalid_seller_rates:,}"
        )
    )

    # ------------------------------------------------------------
    # 15. No negative delivery days
    # ------------------------------------------------------------

    negative_delivery_days = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_orders
        WHERE delivery_days < 0
        """
    ).fetchone()[0]

    results.append(
        check(
            "Delivery days are non-negative",
            negative_delivery_days == 0,
            f"invalid rows={negative_delivery_days:,}"
        )
    )

    # ------------------------------------------------------------
    # 16. Seller count
    # ------------------------------------------------------------

    source_sellers = conn.execute(
        """
        SELECT COUNT(DISTINCT seller_id)
        FROM fact_order_items
        """
    ).fetchone()[0]

    analytical_sellers = conn.execute(
        """
        SELECT COUNT(*)
        FROM seller_delivery_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller delivery table covers all sellers",
            source_sellers == analytical_sellers,
            f"source={source_sellers:,}, analytical={analytical_sellers:,}"
        )
    )

    # ------------------------------------------------------------
    # Final
    # ------------------------------------------------------------

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 70)

    conn.close()

    if passed != total:
        raise SystemExit("Operations analytics validation failed.")

    print("\nOperations analytics validation completed successfully.")


if __name__ == "__main__":
    main()