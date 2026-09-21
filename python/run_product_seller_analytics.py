from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"
SQL_PATH = PROJECT_ROOT / "sql" / "04_product_seller_analytics.sql"


def main():
    print("=" * 70)
    print("PRODUCT & SELLER ANALYTICS")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    try:
        sql = SQL_PATH.read_text(encoding="utf-8")
        conn.execute(sql)

        tables = [
            "category_performance",
            "product_performance",
            "seller_performance",
            "seller_category_performance",
            "seller_state_performance",
        ]

        print("\nAnalytical tables created:")

        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"  {table:<32} {count:>10,} rows")

        print("\nTop product categories by revenue:")

        print(
            conn.execute(
                """
                SELECT
                    product_category,
                    orders,
                    order_items,
                    unique_products,
                    revenue
                FROM category_performance
                ORDER BY revenue DESC
                LIMIT 10
                """
            ).fetchdf().to_string(index=False)
        )

        print("\nTop 10 products by revenue:")

        print(
            conn.execute(
                """
                SELECT
                    product_id,
                    product_category,
                    orders,
                    order_items,
                    revenue
                FROM product_performance
                ORDER BY revenue DESC
                LIMIT 10
                """
            ).fetchdf().to_string(index=False)
        )

        print("\nTop 10 sellers by revenue:")

        print(
            conn.execute(
                """
                SELECT
                    seller_id,
                    seller_state,
                    orders,
                    order_items,
                    unique_products,
                    revenue
                FROM seller_performance
                ORDER BY revenue DESC
                LIMIT 10
                """
            ).fetchdf().to_string(index=False)
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()