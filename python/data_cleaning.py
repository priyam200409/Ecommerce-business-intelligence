from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename):
    """Load a CSV file from the immutable raw-data directory."""

    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def save_processed(df, filename):
    """Save a processed dataframe to data/processed/."""

    output_path = PROCESSED_DIR / filename

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"Saved: {output_path} | "
        f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns"
    )


def clean_string_column(df, column):
    """Standardize string columns without converting missing values to 'nan'."""

    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
    )

    return df


# ============================================================
# 1. ORDERS
# ============================================================

def clean_orders():

    print("\n[1/9] Cleaning orders...")

    orders = load_csv(
        "olist_orders_dataset.csv"
    )

    # --------------------------------------------------------
    # Datetime conversion
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Standardize categorical/string fields
    # --------------------------------------------------------

    string_columns = [
        "order_id",
        "customer_id",
        "order_status"
    ]

    for column in string_columns:

        orders = clean_string_column(
            orders,
            column
        )

    # --------------------------------------------------------
    # Purchase calendar fields
    # --------------------------------------------------------

    orders["order_purchase_date"] = (
        orders["order_purchase_timestamp"]
        .dt.date
    )

    orders["order_purchase_year"] = (
        orders["order_purchase_timestamp"]
        .dt.year
        .astype("Int64")
    )

    orders["order_purchase_month"] = (
        orders["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype("string")
    )

    orders["order_purchase_month_num"] = (
        orders["order_purchase_timestamp"]
        .dt.month
        .astype("Int64")
    )

    orders["order_purchase_day"] = (
        orders["order_purchase_timestamp"]
        .dt.day
        .astype("Int64")
    )

    orders["order_purchase_weekday"] = (
        orders["order_purchase_timestamp"]
        .dt.day_name()
        .astype("string")
    )

    # --------------------------------------------------------
    # Status flags
    # --------------------------------------------------------

    orders["is_delivered"] = (
        orders["order_status"] == "delivered"
    ).astype("boolean")

    orders["is_canceled"] = (
        orders["order_status"] == "canceled"
    ).astype("boolean")

    orders["is_unavailable"] = (
        orders["order_status"] == "unavailable"
    ).astype("boolean")

    # --------------------------------------------------------
    # Delivery duration
    #
    # Purchase → actual customer delivery
    # --------------------------------------------------------

    orders["delivery_days"] = (
        orders["order_delivered_customer_date"]
        - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    orders["delivery_days"] = (
        orders["delivery_days"]
        .round(2)
    )

    # --------------------------------------------------------
    # Expected delivery duration
    #
    # Purchase → estimated delivery
    # --------------------------------------------------------

    orders["estimated_delivery_days"] = (
        orders["order_estimated_delivery_date"]
        - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    orders["estimated_delivery_days"] = (
        orders["estimated_delivery_days"]
        .round(2)
    )

    # --------------------------------------------------------
    # Delivery delay
    #
    # Positive = delivered after estimated date
    # Zero     = delivered on estimated date
    # Negative = delivered before estimated date
    # --------------------------------------------------------

    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"]
        - orders["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    orders["delivery_delay_days"] = (
        orders["delivery_delay_days"]
        .round(2)
    )

    # --------------------------------------------------------
    # Late delivery flag
    #
    # True  = late
    # False = not late
    # <NA>  = actual delivery unavailable
    #
    # Nullable Boolean is intentional.
    # --------------------------------------------------------

    orders["is_late"] = (
        orders["delivery_delay_days"] > 0
    ).astype("boolean")

    orders.loc[
        orders["order_delivered_customer_date"].isna(),
        "is_late"
    ] = pd.NA

    # --------------------------------------------------------
    # Data-quality flags discovered during Day 1
    # --------------------------------------------------------

    orders["flag_carrier_before_purchase"] = (
        orders["order_delivered_carrier_date"].notna()
        & orders["order_purchase_timestamp"].notna()
        & (
            orders["order_delivered_carrier_date"]
            < orders["order_purchase_timestamp"]
        )
    ).astype("boolean")

    orders["flag_carrier_before_approval"] = (
        orders["order_delivered_carrier_date"].notna()
        & orders["order_approved_at"].notna()
        & (
            orders["order_delivered_carrier_date"]
            < orders["order_approved_at"]
        )
    ).astype("boolean")

    orders["flag_delivery_before_carrier"] = (
        orders["order_delivered_customer_date"].notna()
        & orders["order_delivered_carrier_date"].notna()
        & (
            orders["order_delivered_customer_date"]
            < orders["order_delivered_carrier_date"]
        )
    ).astype("boolean")

    # --------------------------------------------------------
    # Overall lifecycle anomaly flag
    # --------------------------------------------------------

    orders["has_date_quality_issue"] = (
        orders[
            [
                "flag_carrier_before_purchase",
                "flag_carrier_before_approval",
                "flag_delivery_before_carrier"
            ]
        ]
        .fillna(False)
        .any(axis=1)
    ).astype("boolean")

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_processed(
        orders,
        "orders_clean.csv"
    )

    return orders


# ============================================================
# 2. ORDER ITEMS
# ============================================================

def clean_order_items():

    print("\n[2/9] Cleaning order items...")

    items = load_csv(
        "olist_order_items_dataset.csv"
    )

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    string_columns = [
        "order_id",
        "product_id",
        "seller_id"
    ]

    for column in string_columns:

        items = clean_string_column(
            items,
            column
        )

    # --------------------------------------------------------
    # Datetime
    # --------------------------------------------------------

    items["shipping_limit_date"] = pd.to_datetime(
        items["shipping_limit_date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    items["order_item_id"] = pd.to_numeric(
        items["order_item_id"],
        errors="coerce"
    ).astype("Int64")

    items["price"] = pd.to_numeric(
        items["price"],
        errors="coerce"
    )

    items["freight_value"] = pd.to_numeric(
        items["freight_value"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Item-level transaction value
    #
    # Revenue from merchandise + freight.
    # We retain both components separately.
    # --------------------------------------------------------

    items["item_total_value"] = (
        items["price"]
        + items["freight_value"]
    )

    items["item_total_value"] = (
        items["item_total_value"]
        .round(2)
    )

    # --------------------------------------------------------
    # Freight ratio
    #
    # freight / product price
    #
    # Undefined when product price = 0.
    # --------------------------------------------------------

    items["freight_ratio"] = np.where(
        items["price"] > 0,
        items["freight_value"] / items["price"],
        np.nan
    )

    items["freight_ratio"] = (
        items["freight_ratio"]
        .round(4)
    )

    save_processed(
        items,
        "order_items_clean.csv"
    )

    return items


# ============================================================
# 3. PAYMENTS
# ============================================================

def clean_payments():

    print("\n[3/9] Cleaning payments...")

    payments = load_csv(
        "olist_order_payments_dataset.csv"
    )

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    string_columns = [
        "order_id",
        "payment_type"
    ]

    for column in string_columns:

        payments = clean_string_column(
            payments,
            column
        )

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    payments["payment_sequential"] = pd.to_numeric(
        payments["payment_sequential"],
        errors="coerce"
    ).astype("Int64")

    payments["payment_installments"] = pd.to_numeric(
        payments["payment_installments"],
        errors="coerce"
    )

    payments["payment_value"] = pd.to_numeric(
        payments["payment_value"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Documented Day 1 anomaly
    #
    # Two credit-card records contain:
    #
    # payment_installments = 0
    #
    # We do not invent a value.
    # Treat zero as missing.
    # --------------------------------------------------------

    zero_installments = (
        payments["payment_installments"] == 0
    )

    payments.loc[
        zero_installments,
        "payment_installments"
    ] = np.nan

    payments["payment_installments"] = (
        payments["payment_installments"]
        .round()
        .astype("Int64")
    )

    # --------------------------------------------------------
    # Payment validity flag
    # --------------------------------------------------------

    payments["has_valid_payment_value"] = (
        payments["payment_value"].notna()
        & (
            payments["payment_value"] >= 0
        )
    ).astype("boolean")

    save_processed(
        payments,
        "payments_clean.csv"
    )

    return payments


# ============================================================
# 4. REVIEWS
# ============================================================

def clean_reviews():

    print("\n[4/9] Cleaning reviews...")

    reviews = load_csv(
        "olist_order_reviews_dataset.csv"
    )

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    string_columns = [
        "review_id",
        "order_id",
        "review_comment_title",
        "review_comment_message"
    ]

    for column in string_columns:

        reviews = clean_string_column(
            reviews,
            column
        )

    # --------------------------------------------------------
    # Datetimes
    # --------------------------------------------------------

    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"],
        errors="coerce"
    )

    reviews["review_answer_timestamp"] = pd.to_datetime(
        reviews["review_answer_timestamp"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Review score
    # --------------------------------------------------------

    reviews["review_score"] = pd.to_numeric(
        reviews["review_score"],
        errors="coerce"
    ).astype("Int64")

    # --------------------------------------------------------
    # Review comment flag
    # --------------------------------------------------------

    reviews["has_review_comment"] = (
        reviews["review_comment_message"].notna()
        & (
            reviews["review_comment_message"]
            .str.strip()
            != ""
        )
    ).astype("boolean")

    save_processed(
        reviews,
        "reviews_clean.csv"
    )

    return reviews


# ============================================================
# 5. CUSTOMERS
# ============================================================

def clean_customers():

    print("\n[5/9] Cleaning customers...")

    customers = load_csv(
        "olist_customers_dataset.csv"
    )

    string_columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]

    for column in string_columns:

        customers = clean_string_column(
            customers,
            column
        )

    save_processed(
        customers,
        "customers_clean.csv"
    )

    return customers


# ============================================================
# 6. PRODUCTS
# ============================================================

def clean_products():

    print("\n[6/9] Cleaning products...")

    products = load_csv(
        "olist_products_dataset.csv"
    )

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    products["product_id"] = clean_string_column(
        products,
        "product_id"
    )["product_id"]

    products["product_category_name"] = (
        products["product_category_name"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    numeric_columns = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]

    for column in numeric_columns:

        products[column] = pd.to_numeric(
            products[column],
            errors="coerce"
        )

    # Integer-like fields
    integer_columns = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty"
    ]

    for column in integer_columns:

        products[column] = (
            products[column]
            .round()
            .astype("Int64")
        )

    save_processed(
        products,
        "products_clean.csv"
    )

    return products


# ============================================================
# 7. SELLERS
# ============================================================

def clean_sellers():

    print("\n[7/9] Cleaning sellers...")

    sellers = load_csv(
        "olist_sellers_dataset.csv"
    )

    string_columns = [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state"
    ]

    for column in string_columns:

        sellers = clean_string_column(
            sellers,
            column
        )

    save_processed(
        sellers,
        "sellers_clean.csv"
    )

    return sellers


# ============================================================
# 8. GEOLOCATION
# ============================================================

def clean_geolocation():

    print("\n[8/9] Cleaning geolocation...")

    geo = load_csv(
        "olist_geolocation_dataset.csv"
    )

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    string_columns = [
        "geolocation_zip_code_prefix",
        "geolocation_city",
        "geolocation_state"
    ]

    for column in string_columns:

        geo = clean_string_column(
            geo,
            column
        )

    # --------------------------------------------------------
    # Coordinate fields
    # --------------------------------------------------------

    geo["geolocation_lat"] = pd.to_numeric(
        geo["geolocation_lat"],
        errors="coerce"
    )

    geo["geolocation_lng"] = pd.to_numeric(
        geo["geolocation_lng"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Day 1 identified substantial duplicate rows and
    # multiple coordinates per ZIP prefix.
    #
    # We deliberately do NOT deduplicate here.
    # That decision belongs to the data-modeling stage.
    # --------------------------------------------------------

    save_processed(
        geo,
        "geolocation_clean.csv"
    )

    return geo


# ============================================================
# 9. CATEGORY TRANSLATION
# ============================================================

def clean_category_translation():

    print("\n[9/9] Cleaning category translation...")

    translation = load_csv(
        "product_category_name_translation.csv"
    )

    translation["product_category_name"] = (
        translation["product_category_name"]
        .astype("string")
        .str.strip()
    )

    translation["product_category_name_english"] = (
        translation["product_category_name_english"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Two source categories have no translation.
    #
    # We retain the original category name.
    # We do not invent an English translation at this stage.
    # --------------------------------------------------------

    save_processed(
        translation,
        "category_translation_clean.csv"
    )

    return translation


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_cleaning_pipeline():

    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("PYTHON DATA CLEANING PIPELINE")
    print("=" * 70)

    clean_orders()
    clean_order_items()
    clean_payments()
    clean_reviews()
    clean_customers()
    clean_products()
    clean_sellers()
    clean_geolocation()
    clean_category_translation()

    print("\n" + "=" * 70)
    print("DATA CLEANING PIPELINE COMPLETED")
    print("=" * 70)

    print("\nProcessed datasets:")

    processed_files = sorted(
        PROCESSED_DIR.glob("*.csv")
    )

    for file_path in processed_files:

        print(
            f"  - {file_path.name}"
        )

    print(
        f"\nTotal processed datasets: "
        f"{len(processed_files)}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_cleaning_pipeline()