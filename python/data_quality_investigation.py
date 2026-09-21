from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def load_data():

    print("\nLoading datasets...")

    data = {
        "orders": load_csv("olist_orders_dataset.csv"),
        "items": load_csv("olist_order_items_dataset.csv"),
        "payments": load_csv("olist_order_payments_dataset.csv"),
        "reviews": load_csv("olist_order_reviews_dataset.csv"),
    }

    print("Datasets loaded successfully.")

    return data


# ============================================================
# 1. INVALID PAYMENT INSTALLMENTS
# ============================================================

def investigate_payment_installments(data):

    print("\n[1/6] Investigating invalid payment installments...")

    payments = data["payments"]

    invalid = payments[
        payments["payment_installments"] <= 0
    ].copy()

    output = REPORT_DIR / "invalid_payment_installments.csv"

    invalid.to_csv(output, index=False)

    print(f"Invalid rows found: {len(invalid)}")
    print(f"Saved to: {output}")

    if not invalid.empty:
        print("\nInvalid payment records:")
        print(invalid.to_string(index=False))


# ============================================================
# 2. INVALID DATE SEQUENCES
# ============================================================

def investigate_date_sequences(data):

    print("\n[2/6] Investigating invalid date sequences...")

    orders = data["orders"].copy()

    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    for column in date_columns:
        orders[column] = pd.to_datetime(
            orders[column],
            errors="coerce"
        )

    investigations = []

    # --------------------------------------------------------
    # Carrier before purchase
    # --------------------------------------------------------

    mask = (
        orders["order_delivered_carrier_date"].notna()
        & orders["order_purchase_timestamp"].notna()
        & (
            orders["order_delivered_carrier_date"]
            < orders["order_purchase_timestamp"]
        )
    )

    temp = orders.loc[
        mask,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ].copy()

    temp["anomaly_type"] = "carrier_before_purchase"

    investigations.append(temp)

    # --------------------------------------------------------
    # Carrier before approval
    # --------------------------------------------------------

    mask = (
        orders["order_delivered_carrier_date"].notna()
        & orders["order_approved_at"].notna()
        & (
            orders["order_delivered_carrier_date"]
            < orders["order_approved_at"]
        )
    )

    temp = orders.loc[
        mask,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ].copy()

    temp["anomaly_type"] = "carrier_before_approval"

    investigations.append(temp)

    # --------------------------------------------------------
    # Customer delivery before purchase
    # --------------------------------------------------------

    mask = (
        orders["order_delivered_customer_date"].notna()
        & orders["order_purchase_timestamp"].notna()
        & (
            orders["order_delivered_customer_date"]
            < orders["order_purchase_timestamp"]
        )
    )

    temp = orders.loc[
        mask,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ].copy()

    temp["anomaly_type"] = "customer_delivery_before_purchase"

    investigations.append(temp)

    # --------------------------------------------------------
    # Customer delivery before carrier
    # --------------------------------------------------------

    mask = (
        orders["order_delivered_customer_date"].notna()
        & orders["order_delivered_carrier_date"].notna()
        & (
            orders["order_delivered_customer_date"]
            < orders["order_delivered_carrier_date"]
        )
    )

    temp = orders.loc[
        mask,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ].copy()

    temp["anomaly_type"] = "customer_delivery_before_carrier"

    investigations.append(temp)

    # --------------------------------------------------------
    # Estimated delivery before purchase
    # --------------------------------------------------------

    mask = (
        orders["order_estimated_delivery_date"].notna()
        & orders["order_purchase_timestamp"].notna()
        & (
            orders["order_estimated_delivery_date"]
            < orders["order_purchase_timestamp"]
        )
    )

    temp = orders.loc[
        mask,
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ].copy()

    temp["anomaly_type"] = "estimated_delivery_before_purchase"

    investigations.append(temp)

    result = pd.concat(
        investigations,
        ignore_index=True
    )

    output = REPORT_DIR / "invalid_date_sequences.csv"

    result.to_csv(
        output,
        index=False
    )

    print(f"Date-sequence anomalies found: {len(result)}")
    print(f"Saved to: {output}")

    if not result.empty:
        print("\nAnomaly counts by type:")
        print(
            result["anomaly_type"]
            .value_counts()
            .to_string()
        )

        print("\nAnomaly counts by order status:")
        print(
            result.groupby(
                ["anomaly_type", "order_status"],
                dropna=False
            )
            .size()
            .rename("orders")
            .reset_index()
            .to_string(index=False)
        )


# ============================================================
# 3. ORDERS WITHOUT ORDER ITEMS
# ============================================================

def investigate_orders_without_items(data):

    print("\n[3/6] Investigating orders without items...")

    orders = data["orders"]
    items = data["items"]

    item_order_ids = set(
        items["order_id"].dropna()
    )

    result = orders[
        ~orders["order_id"].isin(item_order_ids)
    ].copy()

    output = REPORT_DIR / "orders_without_items.csv"

    result.to_csv(output, index=False)

    print(f"Orders without items: {len(result)}")
    print(f"Saved to: {output}")

    if not result.empty:
        print("\nOrder status distribution:")
        print(
            result["order_status"]
            .value_counts(dropna=False)
            .to_string()
        )


# ============================================================
# 4. ORDERS WITHOUT PAYMENTS
# ============================================================

def investigate_orders_without_payments(data):

    print("\n[4/6] Investigating orders without payments...")

    orders = data["orders"]
    payments = data["payments"]

    payment_order_ids = set(
        payments["order_id"].dropna()
    )

    result = orders[
        ~orders["order_id"].isin(payment_order_ids)
    ].copy()

    output = REPORT_DIR / "orders_without_payments.csv"

    result.to_csv(output, index=False)

    print(f"Orders without payments: {len(result)}")
    print(f"Saved to: {output}")

    if not result.empty:
        print("\nOrder status distribution:")
        print(
            result["order_status"]
            .value_counts(dropna=False)
            .to_string()
        )


# ============================================================
# 5. ORDERS WITHOUT REVIEWS
# ============================================================

def investigate_orders_without_reviews(data):

    print("\n[5/6] Investigating orders without reviews...")

    orders = data["orders"]
    reviews = data["reviews"]

    review_order_ids = set(
        reviews["order_id"].dropna()
    )

    result = orders[
        ~orders["order_id"].isin(review_order_ids)
    ].copy()

    output = REPORT_DIR / "orders_without_reviews.csv"

    result.to_csv(output, index=False)

    print(f"Orders without reviews: {len(result)}")
    print(f"Saved to: {output}")

    if not result.empty:
        print("\nOrder status distribution:")
        print(
            result["order_status"]
            .value_counts(dropna=False)
            .to_string()
        )


# ============================================================
# 6. MULTIPLE REVIEWS PER ORDER
# ============================================================

def investigate_multiple_reviews(data):

    print("\n[6/6] Investigating multiple reviews per order...")

    reviews = data["reviews"]

    review_counts = (
        reviews.groupby("order_id")
        .size()
        .reset_index(name="review_count")
    )

    result = review_counts[
        review_counts["review_count"] > 1
    ].copy()

    output = REPORT_DIR / "multiple_reviews_per_order.csv"

    result.to_csv(output, index=False)

    print(f"Orders with multiple reviews: {len(result)}")
    print(f"Saved to: {output}")

    if not result.empty:
        print("\nReview-count distribution:")
        print(
            result["review_count"]
            .value_counts()
            .sort_index()
            .to_string()
        )


# ============================================================
# MAIN
# ============================================================

def run_investigation():

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("TARGETED DATA QUALITY INVESTIGATION")
    print("=" * 70)

    data = load_data()

    investigate_payment_installments(data)
    investigate_date_sequences(data)
    investigate_orders_without_items(data)
    investigate_orders_without_payments(data)
    investigate_orders_without_reviews(data)
    investigate_multiple_reviews(data)

    print("\n" + "=" * 70)
    print("TARGETED INVESTIGATION COMPLETED")
    print("=" * 70)

    print("\nGenerated investigation reports:")

    reports = [
        "invalid_payment_installments.csv",
        "invalid_date_sequences.csv",
        "orders_without_items.csv",
        "orders_without_payments.csv",
        "orders_without_reviews.csv",
        "multiple_reviews_per_order.csv"
    ]

    for report in reports:
        print(f"  - reports/{report}")


if __name__ == "__main__":
    run_investigation()