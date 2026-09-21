from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

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
            f"Required processed file not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def save_table(df, filename):
    output_path = PROCESSED_DIR / filename
    df.to_csv(output_path, index=False)

    print(
        f"Saved: {output_path} | "
        f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns"
    )


# ============================================================
# 1. BUILD ORDER-ITEM FACT
# ============================================================

def build_fact_order_items():

    print("\n[1/7] Building fact_order_items...")

    items = load_processed(
        "order_items_clean.csv"
    )

    products = load_processed(
        "products_clean.csv"
    )

    sellers = load_processed(
        "sellers_clean.csv"
    )

    translation = load_processed(
        "category_translation_clean.csv"
    )

    # --------------------------------------------------------
    # Add product attributes
    # --------------------------------------------------------

    product_columns = [
        "product_id",
        "product_category_name",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]

    items = items.merge(
        products[product_columns],
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    # --------------------------------------------------------
    # Add seller attributes
    # --------------------------------------------------------

    seller_columns = [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state"
    ]

    items = items.merge(
        sellers[seller_columns],
        on="seller_id",
        how="left",
        validate="many_to_one"
    )

    # --------------------------------------------------------
    # Add English category where available
    # --------------------------------------------------------

    items = items.merge(
        translation,
        on="product_category_name",
        how="left",
        validate="many_to_one"
    )

    # --------------------------------------------------------
    # Create a controlled category field.
    #
    # Untranslated categories remain identifiable instead
    # of being fabricated.
    # --------------------------------------------------------

    items["product_category"] = (
        items["product_category_name_english"]
        .fillna(items["product_category_name"])
    )

    # --------------------------------------------------------
    # Revenue classification
    #
    # Item-level revenue is based on product price.
    # Freight is kept separately.
    # --------------------------------------------------------

    items["item_revenue"] = items["price"].round(2)

    items["item_freight"] = (
        items["freight_value"]
        .round(2)
    )

    items["item_total_value"] = (
        items["item_revenue"]
        + items["item_freight"]
    ).round(2)

    save_table(
        items,
        "fact_order_items.csv"
    )

    return items


# ============================================================
# 2. AGGREGATE ORDER ITEMS TO ORDER LEVEL
# ============================================================

def build_order_item_aggregation(items):

    print("\n[2/7] Aggregating order items to order level...")

    order_items_agg = (
        items
        .groupby("order_id", as_index=False)
        .agg(
            item_count=(
                "order_item_id",
                "count"
            ),
            unique_products=(
                "product_id",
                "nunique"
            ),
            unique_sellers=(
                "seller_id",
                "nunique"
            ),
            product_revenue=(
                "item_revenue",
                "sum"
            ),
            freight_value=(
                "item_freight",
                "sum"
            ),
            order_item_total_value=(
                "item_total_value",
                "sum"
            )
        )
    )

    numeric_columns = [
        "product_revenue",
        "freight_value",
        "order_item_total_value"
    ]

    for column in numeric_columns:
        order_items_agg[column] = (
            order_items_agg[column]
            .round(2)
        )

    save_table(
        order_items_agg,
        "agg_order_items.csv"
    )

    return order_items_agg


# ============================================================
# 3. AGGREGATE PAYMENTS
# ============================================================

def build_payment_aggregation():

    print("\n[3/7] Building aggregated payment table...")

    payments = load_processed(
        "payments_clean.csv"
    )

    # --------------------------------------------------------
    # Payment types per order
    # --------------------------------------------------------

    payment_type_summary = (
        payments
        .groupby("order_id")["payment_type"]
        .agg(
            lambda x: " | ".join(
                sorted(
                    x.dropna()
                    .astype(str)
                    .unique()
                )
            )
        )
        .rename("payment_types")
        .reset_index()
    )

    # --------------------------------------------------------
    # Numeric payment aggregation
    # --------------------------------------------------------

    payment_agg = (
        payments
        .groupby("order_id", as_index=False)
        .agg(
            payment_count=(
                "payment_sequential",
                "count"
            ),
            total_payment_value=(
                "payment_value",
                "sum"
            ),
            max_payment_installments=(
                "payment_installments",
                "max"
            )
        )
    )

    payment_agg = payment_agg.merge(
        payment_type_summary,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    payment_agg["total_payment_value"] = (
        payment_agg["total_payment_value"]
        .round(2)
    )

    save_table(
        payment_agg,
        "agg_order_payments.csv"
    )

    return payment_agg


# ============================================================
# 4. AGGREGATE REVIEWS
# ============================================================

def build_review_aggregation():

    print("\n[4/7] Building aggregated review table...")

    reviews = load_processed(
        "reviews_clean.csv"
    )

    # --------------------------------------------------------
    # Aggregate all review scores for an order.
    #
    # We do NOT arbitrarily select one review when multiple
    # reviews exist.
    # --------------------------------------------------------

    review_agg = (
        reviews
        .groupby("order_id", as_index=False)
        .agg(
            review_count=(
                "review_id",
                "count"
            ),
            average_review_score=(
                "review_score",
                "mean"
            ),
            min_review_score=(
                "review_score",
                "min"
            ),
            max_review_score=(
                "review_score",
                "max"
            ),
            review_comment_count=(
                "has_review_comment",
                "sum"
            )
        )
    )

    review_agg["average_review_score"] = (
        review_agg["average_review_score"]
        .round(2)
    )

    save_table(
        review_agg,
        "agg_order_reviews.csv"
    )

    return review_agg


# ============================================================
# 5. BUILD ORDER-LEVEL FACT
# ============================================================

def build_fact_orders(
    order_items_agg,
    payment_agg,
    review_agg
):

    print("\n[5/7] Building fact_orders...")

    orders = load_processed(
        "orders_clean.csv"
    )

    customers = load_processed(
        "customers_clean.csv"
    )

    # --------------------------------------------------------
    # Add customer identity
    # --------------------------------------------------------

    customer_columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]

    orders = orders.merge(
        customers[customer_columns],
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Add order-item aggregates
    # --------------------------------------------------------

    orders = orders.merge(
        order_items_agg,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Add payment aggregates
    # --------------------------------------------------------

    orders = orders.merge(
        payment_agg,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Add review aggregates
    # --------------------------------------------------------

    orders = orders.merge(
        review_agg,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Orders without items remain in the dataset.
    #
    # Therefore item-derived metrics are intentionally missing
    # rather than converted to zero.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Useful order-level business measures
    # --------------------------------------------------------

    orders["freight_ratio"] = np.where(
        orders["product_revenue"] > 0,
        orders["freight_value"]
        / orders["product_revenue"],
        np.nan
    )

    orders["freight_ratio"] = (
        orders["freight_ratio"]
        .round(4)
    )

    orders["revenue_payment_difference"] = (
        orders["total_payment_value"]
        - orders["order_item_total_value"]
    ).round(2)

    # --------------------------------------------------------
    # Customer-level order flags
    # --------------------------------------------------------

    orders["has_items"] = (
        orders["item_count"]
        .notna()
    ).astype("boolean")

    orders["has_payment"] = (
        orders["payment_count"]
        .notna()
    ).astype("boolean")

    orders["has_review"] = (
        orders["review_count"]
        .notna()
    ).astype("boolean")

    save_table(
        orders,
        "fact_orders.csv"
    )

    return orders


# ============================================================
# 6. BUILD CUSTOMER DIMENSION
# ============================================================

def build_dim_customers(fact_orders):

    print("\n[6/7] Building dim_customers...")

    customers = load_processed(
        "customers_clean.csv"
    )

    # --------------------------------------------------------
    # Aggregate order-level behavior by customer_unique_id.
    #
    # This is the actual customer identity used for RFM.
    # --------------------------------------------------------

    customer_orders = (
        fact_orders
        .groupby(
            "customer_unique_id",
            as_index=False
        )
        .agg(
            order_count=(
                "order_id",
                "nunique"
            ),
            first_order_date=(
                "order_purchase_timestamp",
                "min"
            ),
            last_order_date=(
                "order_purchase_timestamp",
                "max"
            ),
            total_product_revenue=(
                "product_revenue",
                "sum"
            ),
            total_freight=(
                "freight_value",
                "sum"
            ),
            total_order_value=(
                "order_item_total_value",
                "sum"
            ),
            average_order_value=(
                "order_item_total_value",
                "mean"
            )
        )
    )

    customer_orders["total_product_revenue"] = (
        customer_orders["total_product_revenue"]
        .round(2)
    )

    customer_orders["total_freight"] = (
        customer_orders["total_freight"]
        .round(2)
    )

    customer_orders["total_order_value"] = (
        customer_orders["total_order_value"]
        .round(2)
    )

    customer_orders["average_order_value"] = (
        customer_orders["average_order_value"]
        .round(2)
    )

    # --------------------------------------------------------
    # Obtain one customer profile record per unique customer.
    #
    # A customer_unique_id can have multiple customer_id
    # records, so we use the latest available customer record
    # deterministically.
    # --------------------------------------------------------

    customer_profile = (
        customers
        .sort_values(
            ["customer_unique_id", "customer_id"]
        )
        .drop_duplicates(
            subset=["customer_unique_id"],
            keep="last"
        )
    )

    profile_columns = [
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]

    customer_profile = customer_profile[
        profile_columns
    ]

    dim_customers = customer_orders.merge(
        customer_profile,
        on="customer_unique_id",
        how="left",
        validate="one_to_one"
    )

    save_table(
        dim_customers,
        "dim_customers.csv"
    )

    return dim_customers


# ============================================================
# 7. ANALYTICAL-LAYER VALIDATION
# ============================================================

def validate_analytical_tables(
    fact_order_items,
    order_items_agg,
    payment_agg,
    review_agg,
    fact_orders,
    dim_customers
):

    print("\n[7/7] Validating analytical tables...")

    results = []

    def check(
        name,
        passed,
        details
    ):
        results.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "details": details
        })

    # --------------------------------------------------------
    # fact_order_items
    # --------------------------------------------------------

    check(
        "fact_order_items row count",
        len(fact_order_items) == 112650,
        f"Rows={len(fact_order_items):,}"
    )

    check(
        "fact_order_items business key",
        fact_order_items.duplicated(
            subset=[
                "order_id",
                "order_item_id"
            ]
        ).sum() == 0,
        "order_id + order_item_id remains unique"
    )

    # --------------------------------------------------------
    # Order-item aggregation
    # --------------------------------------------------------

    check(
        "agg_order_items unique order_id",
        order_items_agg["order_id"].is_unique,
        "One row per order"
    )

    check(
        "order item count preserved",
        order_items_agg["item_count"].sum()
        == len(fact_order_items),
        (
            f"Aggregated items="
            f"{order_items_agg['item_count'].sum():,}; "
            f"detail rows="
            f"{len(fact_order_items):,}"
        )
    )

    # --------------------------------------------------------
    # Payments
    # --------------------------------------------------------

    check(
        "agg_order_payments unique order_id",
        payment_agg["order_id"].is_unique,
        "One row per order"
    )

    # --------------------------------------------------------
    # Reviews
    # --------------------------------------------------------

    check(
        "agg_order_reviews unique order_id",
        review_agg["order_id"].is_unique,
        "One row per order"
    )

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    check(
        "fact_orders row count",
        len(fact_orders) == 99441,
        f"Rows={len(fact_orders):,}"
    )

    check(
        "fact_orders unique order_id",
        fact_orders["order_id"].is_unique,
        "One row per order"
    )

    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    check(
        "dim_customers unique customer_unique_id",
        dim_customers[
            "customer_unique_id"
        ].is_unique,
        "One row per actual customer identity"
    )

    # --------------------------------------------------------
    # Revenue reconciliation
    # --------------------------------------------------------

    detail_revenue = (
        fact_order_items["item_revenue"]
        .sum()
    )

    aggregated_revenue = (
        order_items_agg["product_revenue"]
        .sum()
    )

    check(
        "product revenue reconciliation",
        np.isclose(
            detail_revenue,
            aggregated_revenue
        ),
        (
            f"Detail={detail_revenue:,.2f}; "
            f"Aggregated={aggregated_revenue:,.2f}"
        )
    )

    # --------------------------------------------------------
    # Freight reconciliation
    # --------------------------------------------------------

    detail_freight = (
        fact_order_items["item_freight"]
        .sum()
    )

    aggregated_freight = (
        order_items_agg["freight_value"]
        .sum()
    )

    check(
        "freight reconciliation",
        np.isclose(
            detail_freight,
            aggregated_freight
        ),
        (
            f"Detail={detail_freight:,.2f}; "
            f"Aggregated={aggregated_freight:,.2f}"
        )
    )

    # --------------------------------------------------------
    # Order count relationship
    # --------------------------------------------------------

    check(
        "orders with items represented",
        (
            fact_orders["has_items"]
            .sum()
            == len(order_items_agg)
        ),
        (
            f"Orders with items="
            f"{fact_orders['has_items'].sum():,}; "
            f"aggregated item orders="
            f"{len(order_items_agg):,}"
        )
    )

    validation = pd.DataFrame(results)

    output = (
        REPORT_DIR
        / "analytical_layer_validation.csv"
    )

    validation.to_csv(
        output,
        index=False
    )

    print(
        f"\nValidation report saved to: {output}"
    )

    print("\nAnalytical Layer Validation:")
    print(
        validation.to_string(index=False)
    )

    failures = (
        validation["status"] == "FAIL"
    ).sum()

    if failures > 0:
        raise ValueError(
            f"Analytical layer validation failed "
            f"with {failures} failure(s)."
        )

    print(
        "\nAll analytical-layer validations passed."
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("ANALYTICAL DATA MODEL PIPELINE")
    print("=" * 70)

    # 1. Detailed order-item fact
    fact_order_items = build_fact_order_items()

    # 2. Order-item aggregation
    order_items_agg = build_order_item_aggregation(
        fact_order_items
    )

    # 3. Payment aggregation
    payment_agg = build_payment_aggregation()

    # 4. Review aggregation
    review_agg = build_review_aggregation()

    # 5. Order-level fact
    fact_orders = build_fact_orders(
        order_items_agg,
        payment_agg,
        review_agg
    )

    # 6. Customer dimension
    dim_customers = build_dim_customers(
        fact_orders
    )

    # 7. Validation
    validate_analytical_tables(
        fact_order_items,
        order_items_agg,
        payment_agg,
        review_agg,
        fact_orders,
        dim_customers
    )

    print("\n" + "=" * 70)
    print("ANALYTICAL DATA MODEL COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()