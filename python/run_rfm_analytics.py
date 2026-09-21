from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"
SQL_PATH = PROJECT_ROOT / "sql" / "03_customer_rfm.sql"


def main():
    print("=" * 70)
    print("CUSTOMER RFM ANALYTICS")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    try:
        sql = SQL_PATH.read_text(encoding="utf-8")

        conn.execute(sql)

        print("\nRFM analytical table created successfully.")
        print("\nTable: customer_rfm")

        row_count = conn.execute(
            "SELECT COUNT(*) FROM customer_rfm"
        ).fetchone()[0]

        print(f"Rows: {row_count:,}")

        print("\nRFM segment summary:")
        print(
            conn.execute(
                """
                SELECT
                    customer_segment,
                    COUNT(*) AS customers,
                    ROUND(SUM(monetary), 2) AS revenue,
                    ROUND(AVG(monetary), 2) AS average_customer_revenue
                FROM customer_rfm
                GROUP BY customer_segment
                ORDER BY revenue DESC
                """
            ).fetchdf().to_string(index=False)
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()