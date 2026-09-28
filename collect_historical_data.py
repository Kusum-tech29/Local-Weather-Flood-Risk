import requests
import csv
import os
from datetime import datetime, timedelta


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

    daily_data = {}

    for i, time_value in enumerate(times):
        date_value = time_value[:10]

        if date_value not in daily_data:
            daily_data[date_value] = {
                "precipitation": [],
                "humidity": [],
                "temperature": []
            }

        daily_data[date_value]["precipitation"].append(
            precipitation[i] or 0
        )

        daily_data[date_value]["humidity"].append(
            humidity[i] or 0
        )

        daily_data[date_value]["temperature"].append(
            temperature[i] or 0
        )

    rows = []

    sorted_dates = sorted(daily_data.keys())

    for index, date_value in enumerate(sorted_dates):

        if index < 3:
            continue

        current_day = daily_data[date_value]

        rainfall_24h = sum(current_day["precipitation"])

        previous_dates = sorted_dates[index - 2:index + 1]

        rainfall_72h = 0

        for previous_date in previous_dates:
            rainfall_72h += sum(
                daily_data[previous_date]["precipitation"]
            )

        max_hourly_rain = max(
            current_day["precipitation"]
        )

        avg_humidity = sum(
            current_day["humidity"]
        ) / len(current_day["humidity"])

        avg_temperature = sum(
            current_day["temperature"]
        ) / len(current_day["temperature"])

        current_rain = current_day["precipitation"][-1]

        # Preliminary label generation.
        # This is NOT a scientifically validated flood label.
        if (
            rainfall_24h >= 100
            or rainfall_72h >= 200
            or max_hourly_rain >= 50
        ):
            flood_risk = "HIGH"

        elif (
            rainfall_24h >= 50
            or rainfall_72h >= 100
            or max_hourly_rain >= 30
        ):
            flood_risk = "MEDIUM"

        else:
            flood_risk = "LOW"

        rows.append([
            round(rainfall_24h, 2),
            round(rainfall_72h, 2),
            round(max_hourly_rain, 2),
            round(avg_humidity, 2),
            round(avg_temperature, 2),
            round(current_rain, 2),
            flood_risk
        ])

    return rows


def main():

    print("Downloading historical weather data...")
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
        response = requests.get(
            API_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        rows = calculate_features(data["hourly"])

        os.makedirs("data", exist_ok=True)

        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
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
        print("Historical dataset created successfully!")
        print(f"Rows generated: {len(rows)}")
        print(f"File: {OUTPUT_FILE}")

    except requests.exceptions.RequestException as error:

        print()
        print("Failed to download historical data.")
        print("Error:", error)

    except KeyError as error:

        print()
        print("Unexpected API response.")
        print("Missing field:", error)


if __name__ == "__main__":
    main()