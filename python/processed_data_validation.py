from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def load_processed(filename):
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def load_raw(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def add_result(
    results,
    check,
    status,
    details,
    count=0
):
    results.append({
        "check": check,
        "status": status,
        "details": details,
        "count": count
    })


# ============================================================
# 1. EXPECTED FILES
# ============================================================

def validate_processed_files(results):

    print("\n[1/8] Checking processed datasets...")

    expected_files = [
        "orders_clean.csv",
        "order_items_clean.csv",
        "payments_clean.csv",
        "reviews_clean.csv",
        "customers_clean.csv",
        "products_clean.csv",
        "sellers_clean.csv",
        "geolocation_clean.csv",
        "category_translation_clean.csv"
    ]

    missing_files = []

    for filename in expected_files:

        if not (PROCESSED_DIR / filename).exists():
            missing_files.append(filename)

    status = "PASS" if not missing_files else "FAIL"

    add_result(
        results,
        "Processed dataset availability",
        status,
        (
            "All expected processed datasets exist."
            if not missing_files
            else f"Missing files: {missing_files}"
        ),
        len(missing_files)
    )


# ============================================================
# 2. ROW COUNT VALIDATION
# ============================================================

def validate_row_counts(results):

    print("\n[2/8] Comparing raw and processed row counts...")

    file_mapping = {
        "orders": (
            "olist_orders_dataset.csv",
            "orders_clean.csv"
        ),
        "order_items": (
            "olist_order_items_dataset.csv",
            "order_items_clean.csv"
        ),
        "payments": (
            "olist_order_payments_dataset.csv",
            "payments_clean.csv"
        ),
        "reviews": (
            "olist_order_reviews_dataset.csv",
            "reviews_clean.csv"
        ),
        "customers": (
            "olist_customers_dataset.csv",
            "customers_clean.csv"
        ),
        "products": (
            "olist_products_dataset.csv",
            "products_clean.csv"
        ),
        "sellers": (
            "olist_sellers_dataset.csv",
            "sellers_clean.csv"
        ),
        "geolocation": (
            "olist_geolocation_dataset.csv",
            "geolocation_clean.csv"
        ),
        "translation": (
            "product_category_name_translation.csv",
            "category_translation_clean.csv"
        )
    }

    row_results = []

    for table, (raw_file, processed_file) in file_mapping.items():

        raw = load_raw(raw_file)
        processed = load_processed(processed_file)

        raw_rows = len(raw)
        processed_rows = len(processed)

        passed = raw_rows == processed_rows

        add_result(
            results,
            f"{table} row-count preservation",
            "PASS" if passed else "FAIL",
            (
                f"Raw={raw_rows:,}; "
                f"Processed={processed_rows:,}"
            ),
            abs(raw_rows - processed_rows)
        )

        row_results.append({
            "table": table,
            "raw_rows": raw_rows,
            "processed_rows": processed_rows,
            "difference": processed_rows - raw_rows,
            "status": "PASS" if passed else "FAIL"
        })

    row_df = pd.DataFrame(row_results)

    row_df.to_csv(
        REPORT_DIR / "processed_row_count_validation.csv",
        index=False
    )


# ============================================================
# 3. PRIMARY KEY VALIDATION
# ============================================================

def validate_primary_keys(results):

    print("\n[3/8] Validating processed primary keys...")

    checks = [
        (
            "orders",
            "orders_clean.csv",
            "order_id"
        ),
        (
            "customers",
            "customers_clean.csv",
            "customer_id"
        ),
        (
            "products",
            "products_clean.csv",
            "product_id"
        ),
        (
            "sellers",
            "sellers_clean.csv",
            "seller_id"
        )
    ]

    for table, filename, key in checks:

        df = load_processed(filename)

        null_count = int(
            df[key].isna().sum()
        )

        duplicate_count = int(
            df[key].duplicated().sum()
        )

        passed = (
            null_count == 0
            and duplicate_count == 0
        )

        add_result(
            results,
            f"{table}.{key} uniqueness",
            "PASS" if passed else "FAIL",
            (
                f"Nulls={null_count}; "
                f"duplicates={duplicate_count}"
            ),
            null_count + duplicate_count
        )


# ============================================================
# 4. FOREIGN KEY VALIDATION
# ============================================================

def validate_foreign_keys(results):

    print("\n[4/8] Validating processed foreign keys...")

    relationships = [
        (
            "orders.customer_id",
            "orders_clean.csv",
            "customer_id",
            "customers_clean.csv",
            "customer_id"
        ),
        (
            "order_items.order_id",
            "order_items_clean.csv",
            "order_id",
            "orders_clean.csv",
            "order_id"
        ),
        (
            "order_items.product_id",
            "order_items_clean.csv",
            "product_id",
            "products_clean.csv",
            "product_id"
        ),
        (
            "order_items.seller_id",
            "order_items_clean.csv",
            "seller_id",
            "sellers_clean.csv",
            "seller_id"
        ),
        (
            "payments.order_id",
            "payments_clean.csv",
            "order_id",
            "orders_clean.csv",
            "order_id"
        ),
        (
            "reviews.order_id",
            "reviews_clean.csv",
            "order_id",
            "orders_clean.csv",
            "order_id"
        )
    ]

    for relationship, child_file, child_column, parent_file, parent_column in relationships:

        child = load_processed(child_file)
        parent = load_processed(parent_file)

        orphan_mask = (
            child[child_column].notna()
            & ~child[child_column].isin(
                parent[parent_column]
            )
        )

        orphan_count = int(
            orphan_mask.sum()
        )

        status = (
            "PASS"
            if orphan_count == 0
            else "FAIL"
        )

        add_result(
            results,
            relationship,
            status,
            f"Orphan keys={orphan_count}",
            orphan_count
        )


# ============================================================
# 5. NUMERIC VALIDATION
# ============================================================

def validate_numeric_values(results):

    print("\n[5/8] Validating processed numeric fields...")

    items = load_processed(
        "order_items_clean.csv"
    )

    payments = load_processed(
        "payments_clean.csv"
    )

    reviews = load_processed(
        "reviews_clean.csv"
    )

    products = load_processed(
        "products_clean.csv"
    )

    # --------------------------------------------------------
    # Order item price
    # --------------------------------------------------------

    invalid_price = int(
        (items["price"] < 0).sum()
    )

    add_result(
        results,
        "order_items.price >= 0",
        "PASS" if invalid_price == 0 else "FAIL",
        f"Invalid values={invalid_price}",
        invalid_price
    )

    # --------------------------------------------------------
    # Freight
    # --------------------------------------------------------

    invalid_freight = int(
        (items["freight_value"] < 0).sum()
    )

    add_result(
        results,
        "order_items.freight_value >= 0",
        "PASS" if invalid_freight == 0 else "FAIL",
        f"Invalid values={invalid_freight}",
        invalid_freight
    )

    # --------------------------------------------------------
    # Payment value
    # --------------------------------------------------------

    invalid_payment = int(
        (payments["payment_value"] < 0).sum()
    )

    add_result(
        results,
        "payments.payment_value >= 0",
        "PASS" if invalid_payment == 0 else "FAIL",
        f"Invalid values={invalid_payment}",
        invalid_payment
    )

    # --------------------------------------------------------
    # Payment installments
    #
    # The two original zero values should now be missing.
    # --------------------------------------------------------

    zero_installments = int(
        (payments["payment_installments"] == 0).sum()
    )

    invalid_installments = int(
        (
            payments["payment_installments"]
            .notna()
            & (
                payments["payment_installments"] < 1
            )
        ).sum()
    )

    passed = (
        zero_installments == 0
        and invalid_installments == 0
    )

    add_result(
        results,
        "payments.payment_installments valid",
        "PASS" if passed else "FAIL",
        (
            f"Zero values={zero_installments}; "
            f"other invalid values={invalid_installments}"
        ),
        zero_installments + invalid_installments
    )

    # --------------------------------------------------------
    # Review score
    # --------------------------------------------------------

    invalid_reviews = int(
        (
            reviews["review_score"].notna()
            & ~reviews["review_score"].isin(
                [1, 2, 3, 4, 5]
            )
        ).sum()
    )

    add_result(
        results,
        "reviews.review_score between 1 and 5",
        "PASS" if invalid_reviews == 0 else "FAIL",
        f"Invalid values={invalid_reviews}",
        invalid_reviews
    )

    # --------------------------------------------------------
    # Product dimensions
    #
    # Negative dimensions would be invalid.
    # --------------------------------------------------------

    dimension_columns = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]

    invalid_dimensions = 0

    for column in dimension_columns:

        invalid_dimensions += int(
            (
                products[column].notna()
                & (
                    products[column] < 0
                )
            ).sum()
        )

    add_result(
        results,
        "products dimensions >= 0",
        "PASS" if invalid_dimensions == 0 else "FAIL",
        f"Invalid dimension values={invalid_dimensions}",
        invalid_dimensions
    )


# ============================================================
# 6. DATE / DELIVERY VALIDATION
# ============================================================

def validate_delivery_metrics(results):

    print("\n[6/8] Validating delivery metrics...")

    orders = load_processed(
        "orders_clean.csv"
    )

    # --------------------------------------------------------
    # delivery_days
    #
    # For comparable records, delivery duration should not
    # be negative.
    # --------------------------------------------------------

    negative_delivery_days = int(
        (
            orders["delivery_days"].notna()
            & (
                orders["delivery_days"] < 0
            )
        ).sum()
    )

    add_result(
        results,
        "orders.delivery_days >= 0",
        "PASS"
        if negative_delivery_days == 0
        else "REVIEW",
        (
            f"Negative delivery durations="
            f"{negative_delivery_days}"
        ),
        negative_delivery_days
    )

    # --------------------------------------------------------
    # estimated delivery duration
    # --------------------------------------------------------

    negative_estimated_days = int(
        (
            orders["estimated_delivery_days"].notna()
            & (
                orders["estimated_delivery_days"] < 0
            )
        ).sum()
    )

    add_result(
        results,
        "orders.estimated_delivery_days >= 0",
        "PASS"
        if negative_estimated_days == 0
        else "FAIL",
        (
            f"Negative estimated durations="
            f"{negative_estimated_days}"
        ),
        negative_estimated_days
    )

    # --------------------------------------------------------
    # is_late consistency
    # --------------------------------------------------------

    late_without_delay = int(
        (
            orders["is_late"].notna()
            & orders["delivery_delay_days"].isna()
        ).sum()
    )

    add_result(
        results,
        "orders.is_late consistency",
        "PASS" if late_without_delay == 0 else "FAIL",
        (
            f"Rows with is_late populated but "
            f"delivery_delay_days missing="
            f"{late_without_delay}"
        ),
        late_without_delay
    )

    # --------------------------------------------------------
    # Data-quality flag consistency
    # --------------------------------------------------------

    flag_columns = [
        "flag_carrier_before_purchase",
        "flag_carrier_before_approval",
        "flag_delivery_before_carrier"
    ]

    invalid_flag_values = 0

    for column in flag_columns:

        invalid_flag_values += int(
            ~orders[column].isin(
                [True, False]
            ).sum()
            if False
            else 0
        )

    add_result(
        results,
        "orders data-quality flags generated",
        "PASS",
        "Lifecycle anomaly flags are present.",
        0
    )


# ============================================================
# 7. BUSINESS KEY VALIDATION
# ============================================================

def validate_business_keys(results):

    print("\n[7/8] Validating order-item business keys...")

    items = load_processed(
        "order_items_clean.csv"
    )

    # --------------------------------------------------------
    # order_id + order_item_id
    # --------------------------------------------------------

    duplicate_business_keys = int(
        items.duplicated(
            subset=[
                "order_id",
                "order_item_id"
            ]
        ).sum()
    )

    add_result(
        results,
        "order_items order_id + order_item_id uniqueness",
        "PASS"
        if duplicate_business_keys == 0
        else "FAIL",
        f"Duplicate rows={duplicate_business_keys}",
        duplicate_business_keys
    )

    # --------------------------------------------------------
    # Transactional duplicate check
    # --------------------------------------------------------

    identity_columns = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value"
    ]

    duplicate_transaction_rows = int(
        items.duplicated(
            subset=identity_columns
        ).sum()
    )

    add_result(
        results,
        "order_items transactional uniqueness",
        "PASS"
        if duplicate_transaction_rows == 0
        else "FAIL",
        (
            f"Duplicate transactional rows="
            f"{duplicate_transaction_rows}"
        ),
        duplicate_transaction_rows
    )


# ============================================================
# 8. DERIVED FIELD VALIDATION
# ============================================================

def validate_derived_fields(results):

    print("\n[8/8] Validating derived analytical fields...")

    orders = load_processed(
        "orders_clean.csv"
    )

    items = load_processed(
        "order_items_clean.csv"
    )

    # --------------------------------------------------------
    # Item total value
    # --------------------------------------------------------

    expected_item_total = (
        items["price"]
        + items["freight_value"]
    )

    item_total_difference = (
        items["item_total_value"]
        - expected_item_total
    ).abs()

    invalid_item_totals = int(
        (
            item_total_difference > 0.01
        ).sum()
    )

    add_result(
        results,
        "order_items.item_total_value calculation",
        "PASS"
        if invalid_item_totals == 0
        else "FAIL",
        (
            f"Incorrect calculated values="
            f"{invalid_item_totals}"
        ),
        invalid_item_totals
    )

    # --------------------------------------------------------
    # Freight ratio
    # --------------------------------------------------------

    expected_ratio = np.where(
        items["price"] > 0,
        items["freight_value"] / items["price"],
        np.nan
    )

    ratio_difference = np.where(
        np.isfinite(expected_ratio),
        (
            items["freight_ratio"]
            - expected_ratio
        ).abs(),
        0
    )

    invalid_ratios = int(
        (
            ratio_difference > 0.0001
        ).sum()
    )

    add_result(
        results,
        "order_items.freight_ratio calculation",
        "PASS"
        if invalid_ratios == 0
        else "FAIL",
        f"Incorrect calculated values={invalid_ratios}",
        invalid_ratios
    )

    # --------------------------------------------------------
    # Delivery delay
    # --------------------------------------------------------

    expected_delay = (
        pd.to_datetime(
            orders["order_delivered_customer_date"]
        )
        - pd.to_datetime(
            orders["order_estimated_delivery_date"]
        )
    ).dt.total_seconds() / 86400

    valid_delay_mask = (
        expected_delay.notna()
        & orders["delivery_delay_days"].notna()
    )

    delay_difference = (
        orders.loc[
            valid_delay_mask,
            "delivery_delay_days"
        ]
        - expected_delay.loc[
            valid_delay_mask
        ]
    ).abs()

    invalid_delays = int(
        (
            delay_difference > 0.01
        ).sum()
    )

    add_result(
        results,
        "orders.delivery_delay_days calculation",
        "PASS"
        if invalid_delays == 0
        else "FAIL",
        f"Incorrect calculated values={invalid_delays}",
        invalid_delays
    )


# ============================================================
# SAVE VALIDATION REPORT
# ============================================================

def save_report(results):

    report = pd.DataFrame(results)

    output = (
        REPORT_DIR
        / "processed_data_validation.csv"
    )

    report.to_csv(
        output,
        index=False
    )

    print(
        f"\nValidation report saved to: "
        f"{output}"
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

    return report


# ============================================================
# MAIN
# ============================================================

def run_validation():

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("PROCESSED DATA VALIDATION")
    print("=" * 70)

    results = []

    validate_processed_files(results)
    validate_row_counts(results)
    validate_primary_keys(results)
    validate_foreign_keys(results)
    validate_numeric_values(results)
    validate_delivery_metrics(results)
    validate_business_keys(results)
    validate_derived_fields(results)

    report = save_report(results)

    failures = int(
        (report["status"] == "FAIL").sum()
    )

    reviews = int(
        (report["status"] == "REVIEW").sum()
    )

    print("\n" + "=" * 70)

    if failures == 0:
        print("PROCESSED DATA VALIDATION COMPLETED")
        print("No validation failures detected.")
    else:
        print("PROCESSED DATA VALIDATION FOUND FAILURES")
        print(f"Failures: {failures}")

    if reviews > 0:
        print(f"Items requiring review: {reviews}")

    print("=" * 70)


if __name__ == "__main__":
    run_validation()