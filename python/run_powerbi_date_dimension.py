from pathlib import Path
import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.duckdb"
SQL_PATH = PROJECT_ROOT / "sql" / "06_powerbi_date_dimension.sql"


def main():
    print("=" * 70)
    print("POWER BI DATE DIMENSION")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    try:
        sql = SQL_PATH.read_text(encoding="utf-8")
        conn.execute(sql)

        count = conn.execute(
            "SELECT COUNT(*) FROM dim_date"
        ).fetchone()[0]

        min_date, max_date = conn.execute(
            """
            SELECT MIN(date), MAX(date)
            FROM dim_date
            """
        ).fetchone()

        print(f"\nRows: {count:,}")
        print(f"Minimum date: {min_date}")
        print(f"Maximum date: {max_date}")

        print("\nSample:")
        print(
            conn.execute(
                """
                SELECT *
                FROM dim_date
                ORDER BY date
                LIMIT 5
                """
            ).fetchdf().to_string(index=False)
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()