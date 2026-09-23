from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "powerbi"


TABLES = [
    "fact_orders",
    "fact_order_items",
    "dim_date",
    "dim_customers",
    "customer_rfm",
    "category_performance",
    "product_performance",
    "seller_performance",
    "operations_summary",
    "monthly_operations",
    "delivery_review_performance",
    "review_score_distribution",
    "customer_state_operations",
    "seller_delivery_performance",
    "seller_state_operations",
    "category_operations",
]


def main():
    print("=" * 70)
    print("POWER BI DATA EXPORT")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))

    try:
        for table in TABLES:
            output_path = OUTPUT_DIR / f"{table}.csv"

            print(f"\nExporting: {table}")

            conn.execute(
                f"""
                COPY (
                    SELECT *
                    FROM {table}
                )
                TO '{output_path.as_posix()}'
                (HEADER, DELIMITER ',')
                """
            )

            row_count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"  Rows: {row_count:,}")
            print(f"  File: {output_path}")

    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("POWER BI EXPORT COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()