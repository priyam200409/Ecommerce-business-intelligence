from pathlib import Path
import duckdb


DB_PATH = Path("data/ecommerce.duckdb")
SQL_FILE = Path("sql/01_database_setup.sql")


def run_sql_file():

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE.resolve()}"
        )

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = duckdb.connect(
        str(DB_PATH)
    )

    try:
        sql = SQL_FILE.read_text(
            encoding="utf-8"
        )

        connection.execute(sql)

        print("=" * 70)
        print("DUCKDB DATABASE SETUP COMPLETED")
        print("=" * 70)

        result = connection.execute(
            """
            SELECT
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """
        ).fetchdf()

        print("\nDatabase tables:")
        print(result.to_string(index=False))

    finally:
        connection.close()


if __name__ == "__main__":
    run_sql_file()