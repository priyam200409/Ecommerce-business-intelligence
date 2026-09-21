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
    print("PRODUCT & SELLER ANALYTICS VALIDATION")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    results = []

    expected_tables = [
        "category_performance",
        "product_performance",
        "seller_performance",
        "seller_category_performance",
        "seller_state_performance",
    ]

    tables = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchdf()["table_name"].tolist()

    # ------------------------------------------------------------
    # 1. Tables exist
    # ------------------------------------------------------------

    for table in expected_tables:
        results.append(
            check(
                f"{table} exists",
                table in tables
            )
        )

    # ------------------------------------------------------------
    # 2. Category order-item reconciliation
    # ------------------------------------------------------------

    category_items = conn.execute(
        """
        SELECT SUM(order_items)
        FROM category_performance
        """
    ).fetchone()[0]

    source_items = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_order_items
        """
    ).fetchone()[0]

    results.append(
        check(
            "Category order-item count reconciles",
            category_items == source_items,
            f"category={category_items:,}, source={source_items:,}"
        )
    )

    # ------------------------------------------------------------
    # 3. Product order-item reconciliation
    # ------------------------------------------------------------

    product_items = conn.execute(
        """
        SELECT SUM(order_items)
        FROM product_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Product order-item count reconciles",
            product_items == source_items,
            f"product={product_items:,}, source={source_items:,}"
        )
    )

    # ------------------------------------------------------------
    # 4. Seller order-item reconciliation
    # ------------------------------------------------------------

    seller_items = conn.execute(
        """
        SELECT SUM(order_items)
        FROM seller_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller order-item count reconciles",
            seller_items == source_items,
            f"seller={seller_items:,}, source={source_items:,}"
        )
    )

    # ------------------------------------------------------------
    # 5. Seller category reconciliation
    # ------------------------------------------------------------

    seller_category_items = conn.execute(
        """
        SELECT SUM(order_items)
        FROM seller_category_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller-category order-item count reconciles",
            seller_category_items == source_items,
            f"seller_category={seller_category_items:,}, source={source_items:,}"
        )
    )

    # ------------------------------------------------------------
    # 6. Category revenue reconciliation
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
        FROM category_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Category revenue reconciles",
            abs(source_revenue - category_revenue) < 0.01,
            f"difference={abs(source_revenue - category_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 7. Product revenue reconciliation
    # ------------------------------------------------------------

    product_revenue = conn.execute(
        """
        SELECT SUM(revenue)
        FROM product_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Product revenue reconciles",
            abs(source_revenue - product_revenue) < 0.01,
            f"difference={abs(source_revenue - product_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 8. Seller revenue reconciliation
    # ------------------------------------------------------------

    seller_revenue = conn.execute(
        """
        SELECT SUM(revenue)
        FROM seller_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller revenue reconciles",
            abs(source_revenue - seller_revenue) < 0.01,
            f"difference={abs(source_revenue - seller_revenue):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 9. Category freight reconciliation
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
        FROM category_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Category freight reconciles",
            abs(source_freight - category_freight) < 0.01,
            f"difference={abs(source_freight - category_freight):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 10. Product freight reconciliation
    # ------------------------------------------------------------

    product_freight = conn.execute(
        """
        SELECT SUM(freight)
        FROM product_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Product freight reconciles",
            abs(source_freight - product_freight) < 0.01,
            f"difference={abs(source_freight - product_freight):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 11. Seller freight reconciliation
    # ------------------------------------------------------------

    seller_freight = conn.execute(
        """
        SELECT SUM(freight)
        FROM seller_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller freight reconciles",
            abs(source_freight - seller_freight) < 0.01,
            f"difference={abs(source_freight - seller_freight):.6f}"
        )
    )

    # ------------------------------------------------------------
    # 12. No negative revenue
    # ------------------------------------------------------------

    negative_revenue = conn.execute(
        """
        SELECT COUNT(*)
        FROM product_performance
        WHERE revenue < 0
        """
    ).fetchone()[0]

    results.append(
        check(
            "Product revenue is non-negative",
            negative_revenue == 0,
            f"invalid rows={negative_revenue:,}"
        )
    )

    # ------------------------------------------------------------
    # 13. Seller count reconciliation
    # ------------------------------------------------------------

    seller_count = conn.execute(
        """
        SELECT COUNT(DISTINCT seller_id)
        FROM fact_order_items
        """
    ).fetchone()[0]

    analytical_seller_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM seller_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Seller count reconciles",
            seller_count == analytical_seller_count,
            f"source={seller_count:,}, analytical={analytical_seller_count:,}"
        )
    )

    # ------------------------------------------------------------
    # 14. Product count reconciliation
    # ------------------------------------------------------------

    product_count = conn.execute(
        """
        SELECT COUNT(DISTINCT product_id)
        FROM fact_order_items
        """
    ).fetchone()[0]

    analytical_product_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM product_performance
        """
    ).fetchone()[0]

    results.append(
        check(
            "Product count reconciles",
            product_count == analytical_product_count,
            f"source={product_count:,}, analytical={analytical_product_count:,}"
        )
    )

    # ------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 70)

    conn.close()

    if passed != total:
        raise SystemExit("Product/Seller analytics validation failed.")

    print("\nProduct & Seller analytics validation completed successfully.")


if __name__ == "__main__":
    main()