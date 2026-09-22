from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"
SQL_PATH = PROJECT_ROOT / "sql" / "05_operations_analytics.sql"


def main():
    print("=" * 70)
    print("OPERATIONS & CUSTOMER EXPERIENCE ANALYTICS")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    try:
        sql = SQL_PATH.read_text(encoding="utf-8")
        conn.execute(sql)

        tables = [
            "operations_summary",
            "monthly_operations",
            "customer_state_operations",
            "delivery_review_performance",
            "review_score_distribution",
            "category_operations",
            "seller_delivery_performance",
            "seller_state_operations",
        ]

        print("\nAnalytical tables created:")

        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"  {table:<35} {count:>10,} rows")

        print("\nOverall operations:")
        print(
            conn.execute(
                "SELECT * FROM operations_summary"
            ).fetchdf().to_string(index=False)
        )

        print("\nDelivery vs review:")
        print(
            conn.execute(
                "SELECT * FROM delivery_review_performance"
            ).fetchdf().to_string(index=False)
        )

        print("\nTop customer states by revenue:")
        print(
            conn.execute(
                """
                SELECT
                    customer_state,
                    orders,
                    delivered_orders,
                    revenue,
                    average_delivery_days,
                    late_delivery_rate,
                    average_review_score
                FROM customer_state_operations
                ORDER BY revenue DESC
                LIMIT 10
                """
            ).fetchdf().to_string(index=False)
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()