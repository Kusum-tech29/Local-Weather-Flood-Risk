from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import sqlite3
import joblib
import pandas as pd


load_dotenv()

app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

WEATHER_API_URL = os.getenv("WEATHER_API_URL")
DATABASE_PATH = "flood_risk_history.db"

MODEL_PATH = os.path.join(
    "models",
    "flood_risk_model.joblib"
)


# --------------------------------------------------
# LOAD MACHINE LEARNING MODEL
# --------------------------------------------------

model_package = None
ml_model = None
model_features = None

try:
    model_package = joblib.load(MODEL_PATH)

    ml_model = model_package["model"]
    model_features = model_package["features"]

    print("Flood risk ML model loaded successfully!")

except Exception as error:
    print("WARNING: ML model could not be loaded.")
    print("Error:", error)


# --------------------------------------------------
# HOME ROUTE
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "Local Weather Flood Risk API is running!",
        "ml_model_loaded": ml_model is not None
    })

# --------------------------------------------------
# CITY / LOCATION SEARCH API
# --------------------------------------------------

@app.route("/search-location")
def search_location():

    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({
            "error": "Please provide a city or location name"
        }), 400

    if len(city) < 2:
        return jsonify({
            "error": "City or location name must contain at least 2 characters"
        }), 400

    try:    
        geocoding_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

        params = {
            "name": city,
            "count": 5,
            "language": "en",
            "format": "json"
        }

        response = requests.get(
            geocoding_url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return jsonify({
                "error": "Location not found"
            }), 404

        locations = []

        for place in results:
            locations.append({
                "name": place.get("name"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "country": place.get("country"),
                "state": place.get("admin1"),
                "district": place.get("admin2"),
                "timezone": place.get("timezone")
            })

        return jsonify({
            "query": city,
            "results": locations
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Location search service failed",
            "details": str(error)
        }), 500
    # --------------------------------------------------
# PREDICTION HISTORY DATABASE
# --------------------------------------------------

def init_database():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            flood_risk TEXT NOT NULL,
            confidence REAL,
            rainfall_24h REAL,
            rainfall_72h REAL,
            temperature REAL,
            humidity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()
# --------------------------------------------------
# WEATHER DATA FUNCTION
# --------------------------------------------------

def get_weather_data(latitude, longitude):

    if not WEATHER_API_URL:
        raise ValueError(
            "Weather API URL is not configured"
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "weather_code"
        ),
        "hourly": (
            "precipitation,"
            "rain,"
            "temperature_2m,"
            "relative_humidity_2m"
        ),
        "forecast_days": 3,
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        WEATHER_API_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()
    return response.json()

# --------------------------------------------------
# TERRAIN / ELEVATION DATA
# --------------------------------------------------

def get_elevation_data(latitude, longitude):

    elevation_url = "https://api.open-meteo.com/v1/elevation"

    params = {
        "latitude": latitude,
        "longitude": longitude,
    }

    response = requests.get(
        elevation_url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    elevation_values = data.get("elevation", [])

    if not elevation_values:
        raise ValueError(
            "Elevation data is not available for this location"
        )

    return float(elevation_values[0])
    


# --------------------------------------------------
# WEATHER TEST ROUTE
# --------------------------------------------------

@app.route("/test-weather")
def test_weather():

    latitude = request.args.get(
        "lat",
        type=float
    )

    longitude = request.args.get(
        "lon",
        type=float
    )

    if latitude is None or longitude is None:

        return jsonify({
            "error":
            "Please provide latitude and longitude"
        }), 400

    try:

        weather_data = get_weather_data(
            latitude,
            longitude
        )

        return jsonify({

            "location": {
                "latitude":
                weather_data["latitude"],

                "longitude":
                weather_data["longitude"]
            },

            "current": {
                "temperature":
                weather_data["current"][
                    "temperature_2m"
                ],

                "humidity":
                weather_data["current"][
                    "relative_humidity_2m"
                ],

                "rain":
                weather_data["current"]["rain"],

                "precipitation":
                weather_data["current"][
                    "precipitation"
                ],

                "weather_code":
                weather_data["current"][
                    "weather_code"
                ],

                "time":
                weather_data["current"]["time"]
            },

            "forecast": {
                "time":
                weather_data["hourly"]["time"],

                "precipitation":
                weather_data["hourly"][
                    "precipitation"
                ],

                "rain":
                weather_data["hourly"]["rain"],

                "temperature":
                weather_data["hourly"][
                    "temperature_2m"
                ],

                "humidity":
                weather_data["hourly"][
                    "relative_humidity_2m"
                ]
            },

            "units": {
                "temperature": "°C",
                "humidity": "%",
                "rain": "mm",
                "precipitation": "mm"
            }
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Weather API request failed",
            "details": str(error)
        }), 500

    except KeyError as error:

        return jsonify({
            "error":
            "Unexpected weather data format",

            "details":
            str(error)
        }), 500


# --------------------------------------------------
# ML FLOOD RISK PREDICTION
# --------------------------------------------------
def save_prediction_history(
    latitude,
    longitude,
    flood_risk,
    confidence,
    rainfall_24h,
    rainfall_72h,
    temperature,
    humidity,
):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Remove previous predictions for the same location
    cursor.execute(
        """
        DELETE FROM prediction_history
        WHERE latitude = ? AND longitude = ?
        """,
        (
            latitude,
            longitude,
        ),
    )

    # Save only the latest prediction
    cursor.execute(
        """
        INSERT INTO prediction_history (
            latitude,
            longitude,
            flood_risk,
            confidence,
            rainfall_24h,
            rainfall_72h,
            temperature,
            humidity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            latitude,
            longitude,
            flood_risk,
            confidence,
            rainfall_24h,
            rainfall_72h,
            temperature,
            humidity,
        ),
    )

    connection.commit()
    connection.close()
# --------------------------------------------------
# ML FLOOD RISK PREDICTION
# --------------------------------------------------

def predict_flood_risk(features):

    if ml_model is None:
        raise RuntimeError(
            "Flood risk ML model is not available"
        )

    if not model_features:
        raise RuntimeError(
            "Flood risk model features are not available"
        )

    input_data = pd.DataFrame(
        [features],
        columns=model_features
    )

    prediction = ml_model.predict(
        input_data
    )[0]

    probabilities = ml_model.predict_proba(
        input_data
    )[0]

    probability_map = {}

    for class_name, probability in zip(
        ml_model.classes_,
        probabilities
    ):
        probability_map[str(class_name)] = round(
            float(probability) * 100,
            2
        )

    confidence = round(
        float(max(probabilities)) * 100,
        2
    )

    return (
        str(prediction),
        confidence,
        probability_map
    )


# --------------------------------------------------
# FLOOD RISK API
# --------------------------------------------------

@app.route("/flood-risk")
def flood_risk():

    latitude = request.args.get(
        "lat",
        type=float
    )

    longitude = request.args.get(
        "lon",
        type=float
    )

    # ------------------------------------------
    # COORDINATE VALIDATION
    # ------------------------------------------

    if latitude is None or longitude is None:
        return jsonify({
            "error": "Please provide valid latitude and longitude"
        }), 400

    if not (-90 <= latitude <= 90):
        return jsonify({
            "error": "Latitude must be between -90 and 90"
        }), 400

    if not (-180 <= longitude <= 180):
        return jsonify({
            "error": "Longitude must be between -180 and 180"
        }), 400

    try:

        weather_data = get_weather_data(
            latitude,
            longitude
        )
        elevation = get_elevation_data(
    latitude,
    longitude
)
        current = weather_data["current"]
        hourly = weather_data["hourly"]

        precipitation = [
            value if value is not None else 0
            for value in hourly["precipitation"]
        ]

        if not precipitation:
            raise ValueError(
                "Weather API returned no precipitation forecast data"
            )

        # ------------------------------------------
        # RAINFALL FEATURES
        # ------------------------------------------

        next_24h = precipitation[:24]
        next_72h = precipitation[:72]

        rainfall_24h = round(
            sum(next_24h),
            2
        )

        rainfall_72h = round(
            sum(next_72h),
            2
        )

        max_hourly_rain = round(
            max(precipitation),
            2
        )

        current_humidity = (
            current["relative_humidity_2m"]
        )

        current_temperature = (
            current["temperature_2m"]
        )

        current_rain = (
            current["rain"]
            if current["rain"] is not None
            else 0
        )

        # ------------------------------------------
        # ML FEATURES
        # ------------------------------------------

        features = {
            "rainfall_24h": rainfall_24h,
            "rainfall_72h": rainfall_72h,
            "max_hourly_rain": max_hourly_rain,
            "humidity": current_humidity,
            "temperature": current_temperature,
            "current_rain": current_rain
        }

        # ------------------------------------------
        # MACHINE LEARNING PREDICTION
        # ------------------------------------------

        (
            risk_level,
            confidence,
            probabilities
        ) = predict_flood_risk(features)

        # ------------------------------------------
        # SAVE PREDICTION HISTORY
        # ------------------------------------------

        save_prediction_history(
            latitude=latitude,
            longitude=longitude,
            flood_risk=risk_level,
            confidence=confidence,
            rainfall_24h=rainfall_24h,
            rainfall_72h=rainfall_72h,
            temperature=current_temperature,
            humidity=current_humidity,
        )

        # ------------------------------------------
        # RISK FACTORS
        # ------------------------------------------

        risk_factors = []

        if rainfall_24h >= 35:
            risk_factors.append(
                "Very high rainfall expected "
                "during the next 24 hours"
            )

        elif rainfall_24h >= 16:
            risk_factors.append(
                "Significant rainfall expected "
                "during the next 24 hours"
            )

        if rainfall_72h >= 89:
            risk_factors.append(
                "Very high accumulated rainfall "
                "expected over 72 hours"
            )

        elif rainfall_72h >= 42:
            risk_factors.append(
                "Significant accumulated rainfall "
                "expected over 72 hours"
            )

        if max_hourly_rain >= 12:
            risk_factors.append(
                "High rainfall intensity detected"
            )

        elif max_hourly_rain >= 6:
            risk_factors.append(
                "Moderate rainfall intensity detected"
            )

        if current_humidity >= 90:
            risk_factors.append(
                "Very high humidity"
            )

        elif current_humidity >= 80:
            risk_factors.append(
                "High humidity"
            )

        if current_rain > 0:
            risk_factors.append(
                "Rainfall currently occurring"
            )

        if not risk_factors:
            risk_factors.append(
                "No major rainfall risk factors detected"
            )

        # ------------------------------------------
        # RESPONSE
        # ------------------------------------------

        return jsonify({

            "location": {
                "latitude": weather_data["latitude"],
                "longitude": weather_data["longitude"]
            },

            "prediction": {
                "flood_risk": risk_level,
                "confidence_percent": confidence,
                "class_probabilities": probabilities,
                "model": "Random Forest"
            },

            "rainfall_analysis": {
                "next_24_hours_mm": rainfall_24h,
                "next_72_hours_mm": rainfall_72h,
                "maximum_hourly_rain_mm": max_hourly_rain
            },

            "weather_conditions": {
    "current_temperature_c": current_temperature,
    "current_humidity_percent": current_humidity,
    "current_rain_mm": current_rain,
    "elevation_m": elevation
},

            "risk_factors": risk_factors,

            "disclaimer": (
                "Flood risk is an AI-assisted "
                "rainfall-based risk estimate and "
                "is not an official flood warning."
            )
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Weather API request failed",
            "details": str(error)
        }), 500

    except (
        KeyError,
        ValueError,
        RuntimeError
    ) as error:

        return jsonify({
            "error": "Unable to calculate flood risk",
            "details": str(error)
        }), 500


# --------------------------------------------------
# PREDICTION HISTORY API
# --------------------------------------------------

@app.route("/prediction-history")
def prediction_history():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            latitude,
            longitude,
            flood_risk,
            confidence,
            rainfall_24h,
            rainfall_72h,
            temperature,
            humidity,
            created_at
        FROM prediction_history
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    connection.close()

    history = [
        dict(row)
        for row in rows
    ]

    return jsonify({
        "count": len(history),
        "history": history
    })


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    init_database()
    app.run(debug=True)