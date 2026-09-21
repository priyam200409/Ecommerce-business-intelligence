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
    print("RFM ANALYTICS VALIDATION")
    print("=" * 70)

    conn = duckdb.connect(str(DB_PATH))

    results = []

    # ------------------------------------------------------------
    # 1. Table exists
    # ------------------------------------------------------------
    tables = conn.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchdf()["table_name"].tolist()

    results.append(
        check(
            "customer_rfm table exists",
            "customer_rfm" in tables
        )
    )

    # ------------------------------------------------------------
    # 2. Row count
    # ------------------------------------------------------------
    rfm_count = conn.execute(
        "SELECT COUNT(*) FROM customer_rfm"
    ).fetchone()[0]

    customer_count = conn.execute(
        "SELECT COUNT(*) FROM dim_customers"
    ).fetchone()[0]

    results.append(
        check(
            "RFM row count matches customer dimension",
            rfm_count == customer_count,
            f"RFM={rfm_count:,}, dim_customers={customer_count:,}"
        )
    )

    # ------------------------------------------------------------
    # 3. Unique customers
    # ------------------------------------------------------------
    duplicate_customers = conn.execute(
        """
        SELECT customer_unique_id
        FROM customer_rfm
        GROUP BY customer_unique_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    results.append(
        check(
            "One RFM row per customer",
            len(duplicate_customers) == 0,
            f"duplicate customers={len(duplicate_customers):,}"
        )
    )

    # ------------------------------------------------------------
    # 4. Recency validity
    # ------------------------------------------------------------
    invalid_recency = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE recency < 0
        """
    ).fetchone()[0]

    results.append(
        check(
            "Recency values are non-negative",
            invalid_recency == 0,
            f"invalid rows={invalid_recency:,}"
        )
    )

    # ------------------------------------------------------------
    # 5. Frequency validity
    # ------------------------------------------------------------
    invalid_frequency = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE frequency < 1
        """
    ).fetchone()[0]

    results.append(
        check(
            "Frequency values are valid",
            invalid_frequency == 0,
            f"invalid rows={invalid_frequency:,}"
        )
    )

    # ------------------------------------------------------------
    # 6. Monetary validity
    # ------------------------------------------------------------
    invalid_monetary = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE monetary < 0
        """
    ).fetchone()[0]

    results.append(
        check(
            "Monetary values are non-negative",
            invalid_monetary == 0,
            f"invalid rows={invalid_monetary:,}"
        )
    )

    # ------------------------------------------------------------
    # 7. Recency score
    # ------------------------------------------------------------
    invalid_recency_scores = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE recency_score NOT BETWEEN 1 AND 5
        """
    ).fetchone()[0]

    results.append(
        check(
            "Recency scores are between 1 and 5",
            invalid_recency_scores == 0,
            f"invalid rows={invalid_recency_scores:,}"
        )
    )

    # ------------------------------------------------------------
    # 8. Frequency score
    # ------------------------------------------------------------
    invalid_frequency_scores = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE frequency_score NOT BETWEEN 1 AND 5
        """
    ).fetchone()[0]

    results.append(
        check(
            "Frequency scores are between 1 and 5",
            invalid_frequency_scores == 0,
            f"invalid rows={invalid_frequency_scores:,}"
        )
    )

    # ------------------------------------------------------------
    # 9. Monetary score
    # ------------------------------------------------------------
    invalid_monetary_scores = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE monetary_score NOT BETWEEN 1 AND 5
        """
    ).fetchone()[0]

    results.append(
        check(
            "Monetary scores are between 1 and 5",
            invalid_monetary_scores == 0,
            f"invalid rows={invalid_monetary_scores:,}"
        )
    )

    # ------------------------------------------------------------
    # 10. RFM score format
    # ------------------------------------------------------------
    invalid_rfm_scores = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE LENGTH(rfm_score) != 3
        """
    ).fetchone()[0]

    results.append(
        check(
            "RFM score has three digits",
            invalid_rfm_scores == 0,
            f"invalid rows={invalid_rfm_scores:,}"
        )
    )

    # ------------------------------------------------------------
    # 11. Segment completeness
    # ------------------------------------------------------------
    null_segments = conn.execute(
        """
        SELECT COUNT(*)
        FROM customer_rfm
        WHERE customer_segment IS NULL
        """
    ).fetchone()[0]

    results.append(
        check(
            "Every customer has a segment",
            null_segments == 0,
            f"null segments={null_segments:,}"
        )
    )

    # ------------------------------------------------------------
    # 12. Revenue reconciliation
    # ------------------------------------------------------------
    rfm_revenue = conn.execute(
        """
        SELECT SUM(monetary)
        FROM customer_rfm
        """
    ).fetchone()[0]

    dim_revenue = conn.execute(
        """
        SELECT SUM(total_product_revenue)
        FROM dim_customers
        """
    ).fetchone()[0]

    revenue_difference = abs(rfm_revenue - dim_revenue)

    results.append(
        check(
            "RFM monetary revenue reconciles",
            revenue_difference < 0.01,
            f"difference={revenue_difference:.6f}"
        )
    )

    # ------------------------------------------------------------
    # 13. Segment reconciliation
    # ------------------------------------------------------------
    segment_count = conn.execute(
        """
        SELECT COUNT(DISTINCT customer_segment)
        FROM customer_rfm
        """
    ).fetchone()[0]

    results.append(
        check(
            "Expected RFM segments are present",
            segment_count == 8,
            f"segments={segment_count}"
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

    if passed != total:
        raise SystemExit("RFM validation failed.")

    print("\nRFM analytics validation completed successfully.")

    conn.close()


if __name__ == "__main__":
    main()