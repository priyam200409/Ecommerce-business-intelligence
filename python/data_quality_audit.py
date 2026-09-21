from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename):
    """Load a CSV file from the raw data directory."""
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path.resolve()}")

    return pd.read_csv(path)


def add_quality_result(
    results,
    check,
    status,
    details="",
    count=None,
    percentage=None
):
    """Append a standardized quality result."""
    results.append({
        "check": check,
        "status": status,
        "details": details,
        "count": count,
        "percentage": percentage
    })


def percentage(part, total):
    """Safely calculate percentage."""
    if total == 0:
        return 0.0

    return round((part / total) * 100, 2)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\nLoading raw datasets...")

    data = {
        "orders": load_csv("olist_orders_dataset.csv"),
        "order_items": load_csv("olist_order_items_dataset.csv"),
        "customers": load_csv("olist_customers_dataset.csv"),
        "products": load_csv("olist_products_dataset.csv"),
        "sellers": load_csv("olist_sellers_dataset.csv"),
        "payments": load_csv("olist_order_payments_dataset.csv"),
        "reviews": load_csv("olist_order_reviews_dataset.csv"),
        "geolocation": load_csv("olist_geolocation_dataset.csv"),
        "translation": load_csv(
            "product_category_name_translation.csv"
        )
    }

    print("All datasets loaded successfully.")

    return data


# ============================================================
# 1. PRIMARY KEY QUALITY
# ============================================================

def check_primary_keys(data, results):

    print("\n[1/7] Checking primary keys...")

    primary_keys = {
        "orders": "order_id",
        "customers": "customer_id",
        "products": "product_id",
        "sellers": "seller_id"
    }

    for table_name, key in primary_keys.items():

        df = data[table_name]

        null_count = int(df[key].isna().sum())
        duplicate_count = int(df[key].duplicated().sum())

        total = len(df)

        if null_count == 0 and duplicate_count == 0:
            status = "PASS"
        else:
            status = "FAIL"

        add_quality_result(
            results,
            f"{table_name}.{key} uniqueness",
            status,
            f"Rows={total}, nulls={null_count}, duplicates={duplicate_count}",
            duplicate_count + null_count,
            percentage(duplicate_count + null_count, total)
        )


# ============================================================
# 2. FOREIGN KEY INTEGRITY
# ============================================================

def check_foreign_keys(data, results):

    print("\n[2/7] Checking foreign key integrity...")

    relationships = [
        (
            "orders.customer_id",
            data["orders"]["customer_id"],
            data["customers"]["customer_id"]
        ),
        (
            "order_items.order_id",
            data["order_items"]["order_id"],
            data["orders"]["order_id"]
        ),
        (
            "order_items.product_id",
            data["order_items"]["product_id"],
            data["products"]["product_id"]
        ),
        (
            "order_items.seller_id",
            data["order_items"]["seller_id"],
            data["sellers"]["seller_id"]
        ),
        (
            "payments.order_id",
            data["payments"]["order_id"],
            data["orders"]["order_id"]
        ),
        (
            "reviews.order_id",
            data["reviews"]["order_id"],
            data["orders"]["order_id"]
        )
    ]

    for relationship, child_key, parent_key in relationships:

        orphan_mask = (
            child_key.notna()
            & ~child_key.isin(parent_key)
        )

        orphan_count = int(orphan_mask.sum())

        total_non_null = int(child_key.notna().sum())

        status = "PASS" if orphan_count == 0 else "FAIL"

        add_quality_result(
            results,
            f"{relationship} → parent key",
            status,
            f"Non-null child keys={total_non_null}, orphan keys={orphan_count}",
            orphan_count,
            percentage(orphan_count, total_non_null)
        )


# ============================================================
# 3. NUMERIC / VALUE VALIDATION
# ============================================================

def check_numeric_values(data, results):

    print("\n[3/7] Checking numeric and categorical values...")

    items = data["order_items"]
    payments = data["payments"]
    reviews = data["reviews"]

    # --------------------------------------------------------
    # Order item price
    # --------------------------------------------------------

    invalid_price = int((items["price"] < 0).sum())

    add_quality_result(
        results,
        "order_items.price valid (>= 0)",
        "PASS" if invalid_price == 0 else "FAIL",
        f"Invalid negative prices={invalid_price}",
        invalid_price,
        percentage(invalid_price, len(items))
    )

    # --------------------------------------------------------
    # Freight value
    # --------------------------------------------------------

    invalid_freight = int((items["freight_value"] < 0).sum())

    add_quality_result(
        results,
        "order_items.freight_value valid (>= 0)",
        "PASS" if invalid_freight == 0 else "FAIL",
        f"Invalid negative freight values={invalid_freight}",
        invalid_freight,
        percentage(invalid_freight, len(items))
    )

    # --------------------------------------------------------
    # Payment value
    # --------------------------------------------------------

    invalid_payment_value = int(
        (payments["payment_value"] < 0).sum()
    )

    add_quality_result(
        results,
        "payments.payment_value valid (>= 0)",
        "PASS" if invalid_payment_value == 0 else "FAIL",
        f"Invalid negative payment values={invalid_payment_value}",
        invalid_payment_value,
        percentage(invalid_payment_value, len(payments))
    )

    # --------------------------------------------------------
    # Payment installments
    # --------------------------------------------------------

    invalid_installments_mask = (
        payments["payment_installments"] <= 0
    )

    invalid_installments = int(
        invalid_installments_mask.sum()
    )

    invalid_installment_values = (
        payments.loc[
            invalid_installments_mask,
            "payment_installments"
        ]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    add_quality_result(
        results,
        "payments.payment_installments valid (> 0)",
        "PASS" if invalid_installments == 0 else "REVIEW",
        (
            f"Invalid rows={invalid_installments}; "
            f"invalid values={invalid_installment_values}"
        ),
        invalid_installments,
        percentage(invalid_installments, len(payments))
    )

    # --------------------------------------------------------
    # Review score
    # --------------------------------------------------------

    invalid_review_score_mask = ~reviews["review_score"].isin(
        [1, 2, 3, 4, 5]
    ) & reviews["review_score"].notna()

    invalid_review_scores = int(
        invalid_review_score_mask.sum()
    )

    add_quality_result(
        results,
        "reviews.review_score valid (1-5)",
        "PASS" if invalid_review_scores == 0 else "FAIL",
        f"Invalid review scores={invalid_review_scores}",
        invalid_review_scores,
        percentage(invalid_review_scores, len(reviews))
    )

    # --------------------------------------------------------
    # Payment type
    # --------------------------------------------------------

    expected_payment_types = {
        "credit_card",
        "boleto",
        "voucher",
        "debit_card",
        "not_defined"
    }

    actual_payment_types = set(
        payments["payment_type"]
        .dropna()
        .unique()
    )

    unexpected_payment_types = (
        actual_payment_types - expected_payment_types
    )

    unexpected_payment_count = int(
        payments["payment_type"]
        .isin(unexpected_payment_types)
        .sum()
    )

    status = (
        "PASS"
        if unexpected_payment_count == 0
        else "REVIEW"
    )

    add_quality_result(
        results,
        "payments.payment_type validity",
        status,
        (
            f"Observed types={sorted(actual_payment_types)}; "
            f"unexpected types={sorted(unexpected_payment_types)}"
        ),
        unexpected_payment_count,
        percentage(
            unexpected_payment_count,
            len(payments)
        )
    )


# ============================================================
# 4. MISSING VALUE ANALYSIS
# ============================================================

def analyze_missing_values(data, results):

    print("\n[4/7] Analyzing missing values...")

    missing_results = []

    for table_name, df in data.items():

        for column in df.columns:

            missing_count = int(df[column].isna().sum())

            if missing_count == 0:
                continue

            missing_results.append({
                "table": table_name,
                "column": column,
                "rows": len(df),
                "missing_count": missing_count,
                "missing_percentage": percentage(
                    missing_count,
                    len(df)
                )
            })

    missing_df = pd.DataFrame(missing_results)

    if not missing_df.empty:
        missing_df = missing_df.sort_values(
            ["table", "missing_percentage"],
            ascending=[True, False]
        )

    missing_output = REPORT_DIR / "missing_value_analysis.csv"

    missing_df.to_csv(
        missing_output,
        index=False
    )

    print(
        f"Missing-value report saved to: "
        f"{missing_output}"
    )

    # --------------------------------------------------------
    # Order missing values by order status
    # --------------------------------------------------------

    orders = data["orders"].copy()

    order_missing_columns = [
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date"
    ]

    status_missing_results = []

    for status_value, group in orders.groupby(
        "order_status",
        dropna=False
    ):

        for column in order_missing_columns:

            missing_count = int(group[column].isna().sum())

            status_missing_results.append({
                "order_status": status_value,
                "column": column,
                "orders": len(group),
                "missing_count": missing_count,
                "missing_percentage": percentage(
                    missing_count,
                    len(group)
                )
            })

    status_missing_df = pd.DataFrame(
        status_missing_results
    )

    status_missing_output = (
        REPORT_DIR / "order_missing_by_status.csv"
    )

    status_missing_df.to_csv(
        status_missing_output,
        index=False
    )

    print(
        f"Order-status missingness report saved to: "
        f"{status_missing_output}"
    )

    add_quality_result(
        results,
        "Missing-value analysis",
        "INFO",
        (
            "Missing values documented separately. "
            "No missing values were automatically imputed."
        ),
        int(missing_df["missing_count"].sum())
        if not missing_df.empty else 0,
        None
    )


# ============================================================
# 5. DATE QUALITY / ORDER LIFECYCLE
# ============================================================

def check_date_quality(data, results):

    print("\n[5/7] Checking order lifecycle dates...")

    orders = data["orders"].copy()

    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    # --------------------------------------------------------
    # Parse dates
    # --------------------------------------------------------

    for column in date_columns:

        orders[column] = pd.to_datetime(
            orders[column],
            errors="coerce"
        )

    date_results = []

    for column in date_columns:

        missing_count = int(
            orders[column].isna().sum()
        )

        date_results.append({
            "check": f"{column} missing after parsing",
            "status": "INFO",
            "count": missing_count,
            "percentage": percentage(
                missing_count,
                len(orders)
            ),
            "details": "Missing timestamps retained for semantic analysis."
        })

    # --------------------------------------------------------
    # Invalid date parsing
    # --------------------------------------------------------

    # Original values that are not null but failed parsing
    for column in date_columns:

        original = data["orders"][column]

        parsed = orders[column]

        invalid_parse_mask = (
            original.notna()
            & parsed.isna()
        )

        invalid_parse_count = int(
            invalid_parse_mask.sum()
        )

        status = (
            "PASS"
            if invalid_parse_count == 0
            else "FAIL"
        )

        date_results.append({
            "check": f"{column} parse validity",
            "status": status,
            "count": invalid_parse_count,
            "percentage": percentage(
                invalid_parse_count,
                len(orders)
            ),
            "details": "Non-null values that failed datetime parsing."
        })

    # --------------------------------------------------------
    # Helper for sequence checks
    # --------------------------------------------------------

    sequence_checks = [
        (
            "approved_before_purchase",
            "order_approved_at",
            "order_purchase_timestamp",
            "approved_at < purchase_timestamp"
        ),
        (
            "carrier_before_purchase",
            "order_delivered_carrier_date",
            "order_purchase_timestamp",
            "carrier_date < purchase_timestamp"
        ),
        (
            "carrier_before_approval",
            "order_delivered_carrier_date",
            "order_approved_at",
            "carrier_date < approved_at"
        ),
        (
            "customer_delivery_before_purchase",
            "order_delivered_customer_date",
            "order_purchase_timestamp",
            "customer_delivery < purchase_timestamp"
        ),
        (
            "customer_delivery_before_carrier",
            "order_delivered_customer_date",
            "order_delivered_carrier_date",
            "customer_delivery < carrier_date"
        ),
        (
            "estimated_delivery_before_purchase",
            "order_estimated_delivery_date",
            "order_purchase_timestamp",
            "estimated_delivery < purchase_timestamp"
        )
    ]

    for check_name, first_column, second_column, description in sequence_checks:

        comparable_mask = (
            orders[first_column].notna()
            & orders[second_column].notna()
        )

        invalid_mask = (
            comparable_mask
            & (
                orders[first_column]
                < orders[second_column]
            )
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        comparable_count = int(
            comparable_mask.sum()
        )

        status = (
            "PASS"
            if invalid_count == 0
            else "REVIEW"
        )

        date_results.append({
            "check": check_name,
            "status": status,
            "count": invalid_count,
            "percentage": percentage(
                invalid_count,
                comparable_count
            ),
            "details": (
                f"{description}; "
                f"comparable rows={comparable_count}"
            )
        })

        add_quality_result(
            results,
            check_name,
            status,
            (
                f"{description}; "
                f"comparable rows={comparable_count}"
            ),
            invalid_count,
            percentage(
                invalid_count,
                comparable_count
            )
        )

    # --------------------------------------------------------
    # Date quality report
    # --------------------------------------------------------

    date_quality_df = pd.DataFrame(date_results)

    date_output = REPORT_DIR / "date_quality_results.csv"

    date_quality_df.to_csv(
        date_output,
        index=False
    )

    print(
        f"Date-quality report saved to: "
        f"{date_output}"
    )


# ============================================================
# 6. RELATIONSHIP CARDINALITY
# ============================================================

def check_relationship_cardinality(data):

    print("\n[6/7] Checking relationship cardinality...")

    orders = data["orders"]
    items = data["order_items"]
    payments = data["payments"]
    reviews = data["reviews"]
    customers = data["customers"]
    products = data["products"]
    sellers = data["sellers"]

    relationships = [
        (
            "orders → order_items",
            orders,
            "order_id",
            items,
            "order_id"
        ),
        (
            "orders → payments",
            orders,
            "order_id",
            payments,
            "order_id"
        ),
        (
            "orders → reviews",
            orders,
            "order_id",
            reviews,
            "order_id"
        ),
        (
            "customers → orders",
            customers,
            "customer_id",
            orders,
            "customer_id"
        ),
        (
            "products → order_items",
            products,
            "product_id",
            items,
            "product_id"
        ),
        (
            "sellers → order_items",
            sellers,
            "seller_id",
            items,
            "seller_id"
        )
    ]

    cardinality_results = []

    for relationship, parent_df, parent_key, child_df, child_key in relationships:

        counts = (
            child_df.groupby(child_key)
            .size()
            .rename("child_count")
        )

        parent_counts = (
            parent_df[[parent_key]]
            .drop_duplicates()
            .merge(
                counts,
                how="left",
                left_on=parent_key,
                right_index=True
            )
        )

        parent_counts["child_count"] = (
            parent_counts["child_count"]
            .fillna(0)
            .astype(int)
        )

        zero_count = int(
            (parent_counts["child_count"] == 0).sum()
        )

        one_count = int(
            (parent_counts["child_count"] == 1).sum()
        )

        multiple_count = int(
            (parent_counts["child_count"] > 1).sum()
        )

        max_count = int(
            parent_counts["child_count"].max()
        )

        avg_count = round(
            parent_counts["child_count"].mean(),
            2
        )

        cardinality_results.append({
            "relationship": relationship,
            "parent_rows": len(parent_counts),
            "zero_children": zero_count,
            "one_child": one_count,
            "multiple_children": multiple_count,
            "maximum_children": max_count,
            "average_children": avg_count
        })

    cardinality_df = pd.DataFrame(
        cardinality_results
    )

    output = REPORT_DIR / "relationship_cardinality.csv"

    cardinality_df.to_csv(
        output,
        index=False
    )

    print(
        f"Relationship-cardinality report saved to: "
        f"{output}"
    )

    return cardinality_df


# ============================================================
# 7. GEOLOCATION QUALITY
# ============================================================

def check_geolocation_quality(data, results):

    print("\n[7/7] Investigating geolocation quality...")

    geo = data["geolocation"]

    total_rows = len(geo)

    exact_duplicate_count = int(
        geo.duplicated().sum()
    )

    exact_duplicate_percentage = percentage(
        exact_duplicate_count,
        total_rows
    )

    unique_zip_prefixes = int(
        geo["geolocation_zip_code_prefix"].nunique()
    )

    coordinate_columns = [
        "geolocation_lat",
        "geolocation_lng"
    ]

    missing_coordinates = int(
        geo[coordinate_columns]
        .isna()
        .any(axis=1)
        .sum()
    )

    # --------------------------------------------------------
    # Same ZIP prefix with multiple coordinate pairs
    # --------------------------------------------------------

    coordinate_pairs_per_zip = (
        geo.groupby(
            "geolocation_zip_code_prefix"
        )
        .apply(
            lambda x: x[
                ["geolocation_lat", "geolocation_lng"]
            ]
            .drop_duplicates()
            .shape[0]
        )
        .rename("unique_coordinate_pairs")
        .reset_index()
    )

    zips_with_multiple_coordinates = int(
        (
            coordinate_pairs_per_zip[
                "unique_coordinate_pairs"
            ] > 1
        ).sum()
    )

    max_coordinate_pairs = int(
        coordinate_pairs_per_zip[
            "unique_coordinate_pairs"
        ].max()
    )

    geo_results = pd.DataFrame([
        {
            "metric": "total_rows",
            "value": total_rows
        },
        {
            "metric": "exact_duplicate_rows",
            "value": exact_duplicate_count
        },
        {
            "metric": "exact_duplicate_percentage",
            "value": exact_duplicate_percentage
        },
        {
            "metric": "unique_zip_code_prefixes",
            "value": unique_zip_prefixes
        },
        {
            "metric": "rows_with_missing_coordinates",
            "value": missing_coordinates
        },
        {
            "metric": "zip_prefixes_with_multiple_coordinate_pairs",
            "value": zips_with_multiple_coordinates
        },
        {
            "metric": "maximum_coordinate_pairs_for_one_zip",
            "value": max_coordinate_pairs
        }
    ])

    output = REPORT_DIR / "geolocation_quality.csv"

    geo_results.to_csv(
        output,
        index=False
    )

    print(
        f"Geolocation-quality report saved to: "
        f"{output}"
    )

    add_quality_result(
        results,
        "Geolocation exact duplicates",
        "REVIEW" if exact_duplicate_count > 0 else "PASS",
        (
            f"{exact_duplicate_count:,} exact duplicate rows "
            f"out of {total_rows:,} "
            f"({exact_duplicate_percentage}%). "
            f"No deduplication performed."
        ),
        exact_duplicate_count,
        exact_duplicate_percentage
    )

    add_quality_result(
        results,
        "Geolocation ZIP-prefix coordinate cardinality",
        "INFO",
        (
            f"{zips_with_multiple_coordinates:,} ZIP prefixes "
            f"have multiple unique coordinate pairs."
        ),
        zips_with_multiple_coordinates,
        percentage(
            zips_with_multiple_coordinates,
            unique_zip_prefixes
        )
    )


# ============================================================
# CATEGORY TRANSLATION COVERAGE
# ============================================================

def check_category_translation(data, results):

    print("\nChecking product category translation coverage...")

    products = data["products"]
    translation = data["translation"]

    source_categories = set(
        products["product_category_name"]
        .dropna()
        .unique()
    )

    translated_categories = set(
        translation["product_category_name"]
        .dropna()
        .unique()
    )

    untranslated_categories = sorted(
        source_categories - translated_categories
    )

    add_quality_result(
        results,
        "Product category translation coverage",
        "REVIEW" if untranslated_categories else "PASS",
        (
            f"Source categories={len(source_categories)}, "
            f"translated categories={len(translated_categories)}, "
            f"untranslated categories="
            f"{untranslated_categories}"
        ),
        len(untranslated_categories),
        percentage(
            len(untranslated_categories),
            len(source_categories)
        )
    )

    output = REPORT_DIR / "untranslated_categories.csv"

    pd.DataFrame({
        "untranslated_category": untranslated_categories
    }).to_csv(
        output,
        index=False
    )

    print(
        f"Untranslated-category report saved to: "
        f"{output}"
    )


# ============================================================
# ORDER STATUS DISTRIBUTION
# ============================================================

def analyze_order_status(data, results):

    orders = data["orders"]

    status_distribution = (
        orders["order_status"]
        .value_counts(dropna=False)
        .rename_axis("order_status")
        .reset_index(name="orders")
    )

    status_distribution["percentage"] = (
        status_distribution["orders"]
        .apply(
            lambda x: percentage(x, len(orders))
        )
    )

    output = REPORT_DIR / "order_status_distribution.csv"

    status_distribution.to_csv(
        output,
        index=False
    )

    add_quality_result(
        results,
        "Order status distribution",
        "INFO",
        (
            f"Observed {orders['order_status'].nunique()} "
            f"distinct order statuses."
        ),
        orders["order_status"].nunique(),
        None
    )


# ============================================================
# MAIN AUDIT
# ============================================================

def run_quality_audit():

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("DATA QUALITY AUDIT")
    print("=" * 70)

    data = load_data()

    results = []

    # Core data-quality checks
    check_primary_keys(data, results)
    check_foreign_keys(data, results)
    check_numeric_values(data, results)

    # Missingness and semantic checks
    analyze_missing_values(data, results)
    analyze_order_status(data, results)

    # Temporal validation
    check_date_quality(data, results)

    # Relationship structure
    cardinality_df = check_relationship_cardinality(data)

    # Geolocation
    check_geolocation_quality(data, results)

    # Category mapping
    check_category_translation(data, results)

    # --------------------------------------------------------
    # Save master quality report
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    output = REPORT_DIR / "data_quality_results.csv"

    results_df.to_csv(
        output,
        index=False
    )

    print("\n" + "=" * 70)
    print("DATA QUALITY AUDIT COMPLETED")
    print("=" * 70)

    print(f"\nMaster report: {output}")

    print("\nQuality Summary:")

    print(
        results_df[
            ["status"]
        ]
        .value_counts()
        .to_string()
    )

    print("\nMaster Data Quality Results:")

    print(
        results_df.to_string(index=False)
    )

    print("\nRelationship Cardinality:")

    print(
        cardinality_df.to_string(index=False)
    )

    print("\nGenerated reports:")

    for file_path in sorted(REPORT_DIR.glob("*.csv")):
        print(f"  - {file_path.name}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_quality_audit()