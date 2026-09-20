from pathlib import Path
import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Dataset inventory
# --------------------------------------------------

def profile_dataset():

    results = []

    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR.resolve()}"
        )

    for file_path in csv_files:

        print(f"Profiling: {file_path.name}")

        df = pd.read_csv(file_path)

        results.append({
            "table": file_path.stem,
            "file": file_path.name,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "duplicate_rows": int(df.duplicated().sum()),
            "total_missing_values": int(df.isna().sum().sum()),
            "columns_with_missing_values": int(
                df.isna().any().sum()
            ),
            "memory_mb": round(
                df.memory_usage(deep=True).sum() / (1024 ** 2),
                2
            )
        })

    inventory = pd.DataFrame(results)

    output_file = REPORT_DIR / "table_inventory.csv"

    inventory.to_csv(output_file, index=False)

    print("\nDataset profiling completed.")
    print(f"Report saved to: {output_file}")

    print("\nTable Inventory:")
    print(inventory.to_string(index=False))


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":
    profile_dataset()