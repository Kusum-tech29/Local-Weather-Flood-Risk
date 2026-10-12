
import requests
import csv
import os
from datetime import datetime

API_URL = "https://archive-api.open-meteo.com/v1/archive"

LATITUDE = 26.8467
LONGITUDE = 80.9462

START_DATE = "2021-01-01"
END_DATE = "2025-12-31"

OUTPUT_FILE = "data/flood_risk_data.csv"


def calculate_features(hourly_data):
    times = hourly_data["time"]
    precipitation = hourly_data["precipitation"]
    humidity = hourly_data["relative_humidity_2m"]
    temperature = hourly_data["temperature_2m"]

    rows = []

    # Hourly observations; use rolling windows ending at each hour.
    for i in range(len(times)):
        if i < 71:
            continue

        rainfall_24h_values = precipitation[i - 23:i + 1]
        rainfall_72h_values = precipitation[i - 71:i + 1]

        rainfall_24h = sum(
            value if value is not None else 0
            for value in rainfall_24h_values
        )

        rainfall_72h = sum(
            value if value is not None else 0
            for value in rainfall_72h_values
        )

        max_hourly_rain = max(
            (value if value is not None else 0)
            for value in rainfall_72h_values
        )

        current_humidity = humidity[i]
        current_temperature = temperature[i]
        current_rain = precipitation[i] if precipitation[i] is not None else 0

        # Preliminary rainfall-based proxy labels, not verified flood events.
        if (
            rainfall_24h >= 35
            or rainfall_72h >= 89
            or max_hourly_rain >= 12
        ):
            flood_risk = "HIGH"
        elif (
            rainfall_24h >= 16
            or rainfall_72h >= 42
            or max_hourly_rain >= 6
        ):
            flood_risk = "MEDIUM"
        else:
            flood_risk = "LOW"

        if current_humidity is None or current_temperature is None:
            continue

        rows.append([
            times[i],
            round(rainfall_24h, 2),
            round(rainfall_72h, 2),
            round(max_hourly_rain, 2),
            round(current_humidity, 2),
            round(current_temperature, 2),
            round(current_rain, 2),
            flood_risk
        ])

    return rows


def main():
    print("Downloading historical hourly weather data...")
    print(f"Location: {LATITUDE}, {LONGITUDE}")
    print(f"Period: {START_DATE} to {END_DATE}")

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": (
            "precipitation,"
            "relative_humidity_2m,"
            "temperature_2m"
        ),
        "timezone": "Asia/Kolkata"
    }

    try:
        response = requests.get(API_URL, params=params, timeout=120)
        response.raise_for_status()

        data = response.json()
        rows = calculate_features(data["hourly"])

        if not rows:
            print("No valid hourly records were generated.")
            return

        os.makedirs("data", exist_ok=True)

        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "time",
                "rainfall_24h",
                "rainfall_72h",
                "max_hourly_rain",
                "humidity",
                "temperature",
                "current_rain",
                "flood_risk"
            ])
            writer.writerows(rows)

        print()
        print("Historical hourly dataset created successfully!")
        print(f"Rows generated: {len(rows)}")
        print(f"File: {OUTPUT_FILE}")
        print("Note: flood_risk contains rainfall-based proxy labels.")

    except requests.exceptions.RequestException as error:
        print()
        print("Failed to download historical data.")
        print("Error:", error)

    except (KeyError, TypeError, ValueError) as error:
        print()
        print("Unexpected or incomplete API response.")
        print("Error:", error)


if __name__ == "__main__":
    main()
