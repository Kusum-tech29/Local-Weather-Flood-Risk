import os
import pandas as pd


INPUT_FILE = "data/flood_risk_data.csv"
OUTPUT_FILE = "data/flood_risk_ml_data.csv"


def assign_risk(row):
    """
    Creates preliminary ML labels from the historical
    weather distribution.

    IMPORTANT:
    These are weather-risk proxy labels, not verified
    historical flood-event ground-truth labels.
    """

    rainfall_24h = row["rainfall_24h"]
    rainfall_72h = row["rainfall_72h"]
    max_hourly_rain = row["max_hourly_rain"]

    # HIGH RISK
    # Approximately extreme rainfall conditions
    if (
        rainfall_24h >= 35
        or rainfall_72h >= 89
        or max_hourly_rain >= 12
    ):
        return "HIGH"

    # MEDIUM RISK
    # Significant but less extreme rainfall conditions
    if (
        rainfall_24h >= 16
        or rainfall_72h >= 42
        or max_hourly_rain >= 6
    ):
        return "MEDIUM"

    # LOW RISK
    return "LOW"


def main():

    print("Loading historical dataset...")

    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "rainfall_24h",
        "rainfall_72h",
        "max_hourly_rain",
        "humidity",
        "temperature",
        "current_rain"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("Missing columns:")
        print(missing_columns)
        return

    # Remove rows containing missing feature values
    df = df.dropna(subset=required_columns).copy()

    # Preserve the old label for comparison
    if "flood_risk" in df.columns:
        df = df.rename(
            columns={"flood_risk": "original_risk_label"}
        )

    # Generate improved proxy labels
    df["flood_risk"] = df.apply(
        assign_risk,
        axis=1
    )

    # Save ML-ready dataset
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("ML dataset created successfully!")
    print(f"Rows: {len(df)}")
    print(f"File: {OUTPUT_FILE}")

    print()
    print("New class distribution:")
    print(df["flood_risk"].value_counts())

    print()
    print("Class percentages:")
    percentages = (
        df["flood_risk"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    print(percentages)

    print()
    print(
        "NOTE: These labels represent rainfall-based "
        "weather risk proxies, not verified flood events."
    )


if __name__ == "__main__":
    main()