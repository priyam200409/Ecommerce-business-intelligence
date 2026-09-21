from pathlib import Path

import duckdb


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path("data/ecommerce.duckdb")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


EXPECTED_TABLES = {
    "fact_order_items": 112650,
    "agg_order_items": 98666,
    "agg_order_payments": 99440,
    "agg_order_reviews": 98673,
    "fact_orders": 99441,
    "dim_customers": 96096,
}


# ============================================================
# HELPERS
# ============================================================

def check_result(results, check, passed, details):
    results.append({
        "check": check,
        "status": "PASS" if passed else "FAIL",
        "details": details
    })


# ============================================================
# VALIDATION
# ============================================================

def validate_database():

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DB_PATH.resolve()}"
        )

    connection = duckdb.connect(str(DB_PATH))

    results = []

    try:

        print("=" * 70)
        print("E-COMMERCE BUSINESS INTELLIGENCE")
        print("DUCKDB DATABASE VALIDATION")
        print("=" * 70)

        # ----------------------------------------------------
        # 1. TABLE EXISTENCE
        # ----------------------------------------------------

        print("\n[1/6] Checking expected tables...")

        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """
        ).fetchdf()

        actual_tables = set(
            tables["table_name"].tolist()
        )

        expected_table_names = set(
            EXPECTED_TABLES.keys()
        )

        missing_tables = (
            expected_table_names
            - actual_tables
        )

        unexpected_tables = (
            actual_tables
            - expected_table_names
        )

        check_result(
            results,
            "Expected tables exist",
            len(missing_tables) == 0,
            f"Missing tables={sorted(missing_tables)}"
        )

        check_result(
            results,
            "No unexpected analytical tables",
            len(unexpected_tables) == 0,
            f"Unexpected tables={sorted(unexpected_tables)}"
        )

        # ----------------------------------------------------
        # 2. ROW COUNTS
        # ----------------------------------------------------

        print("\n[2/6] Validating table row counts...")

        for table_name, expected_rows in EXPECTED_TABLES.items():

            actual_rows = connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            check_result(
                results,
                f"{table_name} row count",
                actual_rows == expected_rows,
                (
                    f"Expected={expected_rows:,}; "
                    f"Actual={actual_rows:,}"
                )
            )

        # ----------------------------------------------------
        # 3. GRAIN VALIDATION
        # ----------------------------------------------------

        print("\n[3/6] Validating analytical table grain...")

        queries = {
            "fact_order_items grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT order_id || '-' || order_item_id)
                FROM fact_order_items
                """,

            "fact_orders grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT order_id)
                FROM fact_orders
                """,

            "dim_customers grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT customer_unique_id)
                FROM dim_customers
                """,

            "agg_order_items grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT order_id)
                FROM agg_order_items
                """,

            "agg_order_payments grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT order_id)
                FROM agg_order_payments
                """,

            "agg_order_reviews grain":
                """
                SELECT COUNT(*) = COUNT(DISTINCT order_id)
                FROM agg_order_reviews
                """
        }

        for check_name, query in queries.items():

            passed = bool(
                connection.execute(query).fetchone()[0]
            )

            check_result(
                results,
                check_name,
                passed,
                "Expected analytical grain preserved"
            )

        # ----------------------------------------------------
        # 4. REVENUE RECONCILIATION
        # ----------------------------------------------------

        print("\n[4/6] Validating revenue reconciliation...")

        detail_revenue = connection.execute(
            """
            SELECT ROUND(SUM(item_revenue), 2)
            FROM fact_order_items
            """
        ).fetchone()[0]

        aggregated_revenue = connection.execute(
            """
            SELECT ROUND(SUM(product_revenue), 2)
            FROM agg_order_items
            """
        ).fetchone()[0]

        check_result(
            results,
            "Product revenue reconciliation",
            detail_revenue == aggregated_revenue,
            (
                f"Detail={detail_revenue:,.2f}; "
                f"Aggregated={aggregated_revenue:,.2f}"
            )
        )

        # ----------------------------------------------------
        # 5. FREIGHT RECONCILIATION
        # ----------------------------------------------------

        print("\n[5/6] Validating freight reconciliation...")

        detail_freight = connection.execute(
            """
            SELECT ROUND(SUM(item_freight), 2)
            FROM fact_order_items
            """
        ).fetchone()[0]

        aggregated_freight = connection.execute(
            """
            SELECT ROUND(SUM(freight_value), 2)
            FROM agg_order_items
            """
        ).fetchone()[0]

        check_result(
            results,
            "Freight reconciliation",
            detail_freight == aggregated_freight,
            (
                f"Detail={detail_freight:,.2f}; "
                f"Aggregated={aggregated_freight:,.2f}"
            )
        )

        # ----------------------------------------------------
        # 6. ORDER RELATIONSHIP VALIDATION
        # ----------------------------------------------------

        print("\n[6/6] Validating order relationships...")

        orders_with_items = connection.execute(
            """
            SELECT COUNT(*)
            FROM fact_orders
            WHERE has_items = TRUE
            """
        ).fetchone()[0]

        aggregated_item_orders = connection.execute(
            """
            SELECT COUNT(*)
            FROM agg_order_items
            """
        ).fetchone()[0]

        check_result(
            results,
            "Orders with items relationship",
            orders_with_items == aggregated_item_orders,
            (
                f"Orders with items={orders_with_items:,}; "
                f"Aggregated item orders="
                f"{aggregated_item_orders:,}"
            )
        )

        # ----------------------------------------------------
        # SAVE REPORT
        # ----------------------------------------------------

        import pandas as pd

        report = pd.DataFrame(results)

        report_path = (
            REPORT_DIR
            / "duckdb_validation.csv"
        )

        report.to_csv(
            report_path,
            index=False
        )

        print(
            f"\nValidation report saved to: "
            f"{report_path}"
        )

        print("\nValidation Summary:")

        print(
            report["status"]
            .value_counts()
            .to_string()
        )

        print("\nDetailed Results:")

        print(
            report.to_string(index=False)
        )

        failures = int(
            (report["status"] == "FAIL").sum()
        )

        if failures > 0:
            raise ValueError(
                f"DuckDB validation failed "
                f"with {failures} failure(s)."
            )

        print("\n" + "=" * 70)
        print("DUCKDB VALIDATION COMPLETED")
        print("All validation checks passed.")
        print("=" * 70)

    finally:
        connection.close()


if __name__ == "__main__":
    validate_database()