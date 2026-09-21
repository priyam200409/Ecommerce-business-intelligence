from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path.resolve()}"
        )

    return pd.read_csv(path)


def check_order_items_business_keys():

    print("\nChecking order_items business keys...")

    items = load_csv("olist_order_items_dataset.csv")

    # --------------------------------------------------------
    # Key 1: order_id + order_item_id
    # --------------------------------------------------------

    key_columns = [
        "order_id",
        "order_item_id"
    ]

    duplicate_mask = items.duplicated(
        subset=key_columns,
        keep=False
    )

    duplicate_rows = items.loc[
        duplicate_mask
    ].copy()

    duplicate_groups = (
        items.loc[duplicate_mask]
        .groupby(key_columns)
        .size()
        .reset_index(name="duplicate_count")
    )

    print(
        f"\nDuplicate order_id + order_item_id rows: "
        f"{len(duplicate_rows)}"
    )

    print(
        f"Duplicate key groups: "
        f"{len(duplicate_groups)}"
    )

    # --------------------------------------------------------
    # Key 2: full transactional identity
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

    identity_duplicate_mask = items.duplicated(
        subset=identity_columns,
        keep=False
    )

    identity_duplicates = items.loc[
        identity_duplicate_mask
    ].copy()

    print(
        f"\nExact transactional duplicate rows: "
        f"{len(identity_duplicates)}"
    )

    # --------------------------------------------------------
    # Save reports
    # --------------------------------------------------------

    duplicate_rows.to_csv(
        REPORT_DIR / "order_item_business_key_duplicates.csv",
        index=False
    )

    duplicate_groups.to_csv(
        REPORT_DIR / "order_item_duplicate_key_groups.csv",
        index=False
    )

    identity_duplicates.to_csv(
        REPORT_DIR / "order_item_transactional_duplicates.csv",
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = pd.DataFrame([
        {
            "check": "order_id + order_item_id uniqueness",
            "rows": len(items),
            "duplicate_rows": len(duplicate_rows),
            "duplicate_groups": len(duplicate_groups)
        },
        {
            "check": "full transactional identity uniqueness",
            "rows": len(items),
            "duplicate_rows": len(identity_duplicates),
            "duplicate_groups": (
                identity_duplicates
                .groupby(identity_columns)
                .ngroups
                if not identity_duplicates.empty
                else 0
            )
        }
    ])

    summary.to_csv(
        REPORT_DIR / "business_key_validation.csv",
        index=False
    )

    print("\nBusiness-key validation completed.")

    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    print("=" * 70)
    print("E-COMMERCE BUSINESS INTELLIGENCE")
    print("BUSINESS KEY VALIDATION")
    print("=" * 70)

    check_order_items_business_keys()

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETED")
    print("=" * 70)