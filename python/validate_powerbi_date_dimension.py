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
    print("POWER BI DATE DIMENSION VALIDATION")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    results = []

    # Table exists
    exists = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'dim_date'
        """
    ).fetchone()[0]

    results.append(
        check(
            "dim_date exists",
            exists == 1
        )
    )

    # Row count
    count = conn.execute(
        "SELECT COUNT(*) FROM dim_date"
    ).fetchone()[0]

    min_source, max_source = conn.execute(
        """
        SELECT
            MIN(order_purchase_date),
            MAX(order_purchase_date)
        FROM fact_orders
        """
    ).fetchone()

    expected_days = conn.execute(
        """
        SELECT DATE_DIFF(
            'day',
            ?::DATE,
            ?::DATE
        ) + 1
        """,
        [min_source, max_source]
    ).fetchone()[0]

    results.append(
        check(
            "Date range has no missing days",
            count == expected_days,
            f"actual={count:,}, expected={expected_days:,}"
        )
    )

    # Unique dates
    duplicate_dates = conn.execute(
        """
        SELECT date
        FROM dim_date
        GROUP BY date
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    results.append(
        check(
            "Dates are unique",
            len(duplicate_dates) == 0,
            f"duplicate_dates={len(duplicate_dates):,}"
        )
    )

    # Minimum date
    dim_min = conn.execute(
        "SELECT MIN(date) FROM dim_date"
    ).fetchone()[0]

    results.append(
        check(
            "Minimum date matches source",
            dim_min == min_source,
            f"dimension={dim_min}, source={min_source}"
        )
    )

    # Maximum date
    dim_max = conn.execute(
        "SELECT MAX(date) FROM dim_date"
    ).fetchone()[0]

    results.append(
        check(
            "Maximum date matches source",
            dim_max == max_source,
            f"dimension={dim_max}, source={max_source}"
        )
    )

    # Null dates
    null_dates = conn.execute(
        """
        SELECT COUNT(*)
        FROM dim_date
        WHERE date IS NULL
        """
    ).fetchone()[0]

    results.append(
        check(
            "No null dates",
            null_dates == 0,
            f"null_dates={null_dates:,}"
        )
    )

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 70)

    conn.close()

    if passed != total:
        raise SystemExit("Date dimension validation failed.")

    print("\nPower BI date dimension validation completed successfully.")


if __name__ == "__main__":
    main()