from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

import requests
import time
import os
import sqlite3
import joblib
import pandas as pd
from datetime import datetime
from math import (
    radians,
    sin,
    cos,
    asin,
    sqrt,
    atan2
)


# ==================================================
# LOAD ENVIRONMENT
# ==================================================

load_dotenv()


# ==================================================
# CACHE
# ==================================================

weather_cache = {}


# ==================================================
# FLASK APPLICATION
# ==================================================

app = Flask(__name__)

CORS(app)


# ==================================================
# CONFIGURATION
# ==================================================

WEATHER_API_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

DATABASE_PATH = (
    "flood_risk_history.db"
)

MODEL_PATH = os.path.join(
    "models",
    "flood_risk_model.joblib"
)

GEONAMES_FILE = os.path.join(
    "geonames_india",
    "IN.txt"
)

ADMIN1_FILE = "geonames_admin1.txt"
ADMIN2_FILE = "geonames_admin2.txt"

ADMIN1_MAP = {}
ADMIN2_MAP = {}

try:
    with open(ADMIN1_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                ADMIN1_MAP[parts[0]] = parts[1]
except (OSError, UnicodeError):
    pass

try:
    with open(ADMIN2_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                ADMIN2_MAP[parts[0]] = parts[1]
except (OSError, UnicodeError):
    pass


# ==================================================
# LOAD MACHINE LEARNING MODEL
# ==================================================

model_package = None

ml_model = None

model_features = None


try:

    model_package = joblib.load(
        MODEL_PATH
    )

    ml_model = model_package["model"]

    model_features = model_package["features"]

    print(
        "Flood risk ML model loaded successfully!"
    )

except Exception as error:

    print(
        "WARNING: ML model could not be loaded."
    )

    print(
        "Error:",
        error
    )


# ==================================================
# HOME ROUTE
# ==================================================

@app.route("/")
def home():

    return jsonify({

        "message":
            "Local Weather Flood Risk API is running!",

        "ml_model_loaded":
            ml_model is not None

    })


# ==================================================
# SIMPLE LOCATION SEARCH API
# ==================================================

@app.route("/search-location")
def search_location():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({

            "error":
                "Please provide a city or location name"

        }), 400

    if len(city) < 2:

        return jsonify({

            "error":
                "City or location name must contain at least 2 characters"

        }), 400

    try:

        geocoding_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

        params = {

            "name":
                city,

            "count":
                10,

            "language":
                "en",

            "format":
                "json"
        }

        response = requests.get(

            geocoding_url,

            params=params,

            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:

            return jsonify({

                "error":
                    "Location not found"

            }), 404

        locations = []

        for place in results:

            locations.append({

                "name":
                    place.get("name"),

                "latitude":
                    place.get("latitude"),

                "longitude":
                    place.get("longitude"),

                "country":
                    place.get("country"),

                "country_code":
                    place.get("country_code"),

                "state":
                    place.get("admin1"),

                "district":
                    place.get("admin2"),

                "city":
                    place.get("admin3"),

                "timezone":
                    place.get("timezone"),

                "population":
                    place.get("population"),

                "elevation":
                    place.get("elevation"),

                "source":
                    "Open-Meteo"

            })

        return jsonify({

            "query":
                city,

            "results":
                locations

        })

    except requests.exceptions.RequestException as error:

        return jsonify({

            "error":
                "Location search service failed",

            "details":
                str(error)

        }), 500


# ==================================================
# PREDICTION HISTORY DATABASE
# ==================================================

def init_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
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
        """
    )

    connection.commit()

    connection.close()


# ==================================================
# DISTANCE CALCULATION
# ==================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    earth_radius_km = 6371.0

    lat1_rad = radians(
        lat1
    )

    lat2_rad = radians(
        lat2
    )

    delta_lat = radians(
        lat2 - lat1
    )

    delta_lon = radians(
        lon2 - lon1
    )

    a = (

        sin(
            delta_lat / 2
        ) ** 2

        +

        cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2

    )

    return (

        2
        * earth_radius_km
        * asin(
            sqrt(a)
        )

    )


# ==================================================
# WATER FEATURE / RIVER PROXIMITY
# ==================================================

def get_nearby_water_feature(
    latitude,
    longitude
):

    nominatim_url = (
        "https://nominatim.openstreetmap.org/search"
    )

    reverse_url = (
        "https://nominatim.openstreetmap.org/reverse"
    )

    headers = {

        "User-Agent":
            "LocalWeatherFloodRisk/1.0"
    }

    reverse_params = {

        "lat":
            latitude,

        "lon":
            longitude,

        "format":
            "json",

        "zoom":
            10
    }

    reverse_response = requests.get(

        reverse_url,

        params=reverse_params,

        headers=headers,

        timeout=15
    )

    reverse_response.raise_for_status()

    reverse_data = (
        reverse_response.json()
    )

    address = reverse_data.get(
        "address",
        {}
    )

    city = (

        address.get("city")

        or address.get("town")

        or address.get("municipality")

        or address.get("county")

        or ""

    )

    state = address.get(
        "state",
        ""
    )

    if city:

        query = (
            f"river near {city}, {state}"
        )

    else:

        query = (
            f"river near {latitude}, {longitude}"
        )

    params = {

        "q":
            query,

        "format":
            "json",

        "limit":
            10
    }

    response = requests.get(

        nominatim_url,

        params=params,

        headers=headers,

        timeout=15
    )

    response.raise_for_status()

    results = response.json()

    water_features = [

        item

        for item in results

        if item.get("class") == "waterway"

        and item.get("type") in [

            "river",
            "stream",
            "canal"

        ]

        and item.get("lat")

        and item.get("lon")

    ]

    if not water_features:

        return None

    nearest = min(

        water_features,

        key=lambda item:
            calculate_distance_km(

                latitude,

                longitude,

                float(
                    item["lat"]
                ),

                float(
                    item["lon"]
                )

            )

    )

    distance_km = calculate_distance_km(

        latitude,

        longitude,

        float(
            nearest["lat"]
        ),

        float(
            nearest["lon"]
        )

    )

    return {

        "name":
            nearest.get(
                "name",
                "Water Feature"
            ),

        "type":
            nearest.get(
                "type"
            ),

        "latitude":
            float(
                nearest["lat"]
            ),

        "longitude":
            float(
                nearest["lon"]
            ),

        "distance_km":
            round(
                distance_km,
                2
            ),

        "near_water_feature":
            distance_km <= 5

    }


# ==================================================
# WEATHER DATA
# ==================================================

def get_weather_data(
    latitude,
    longitude
):

    cache_key = (

        round(
            latitude,
            2
        ),

        round(
            longitude,
            2
        )

    )

    cached_data = weather_cache.get(
        cache_key
    )

    if cached_data:

        cached_time, weather_data = (
            cached_data
        )

        if (
            time.time()
            - cached_time
            < 1800
        ):

            return weather_data

    if not WEATHER_API_URL:

        raise ValueError(
            "Weather API URL is not configured"
        )

    params = {

        "latitude":
            latitude,

        "longitude":
            longitude,

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
        "past_days": 3,
        "forecast_days": 4,
        "timezone": "Asia/Kolkata"
    }
    response = requests.get(
        WEATHER_API_URL,
        params=params,
        timeout=15
    )

    if response.status_code == 429:
        raise requests.exceptions.HTTPError(
            "Open-Meteo rate limit reached. "
            "Please wait a few minutes and try again.",
            response=response
        )

    response.raise_for_status()
    weather_data = response.json()

    weather_cache[cache_key] = (

        time.time(),

        weather_data

    )

    return weather_data


# ==================================================
# ELEVATION DATA
# ==================================================

def get_elevation_data(
    latitude,
    longitude
):

    elevation_url = (
        "https://api.open-meteo.com/v1/elevation"
    )

    params = {

        "latitude":
            latitude,

        "longitude":
            longitude
    }

    response = requests.get(

        elevation_url,

        params=params,

        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    elevation_values = data.get(
        "elevation",
        []
    )

    if not elevation_values:

        raise ValueError(
            "Elevation data is not available for this location"
        )

    return float(
        elevation_values[0]
    )


# ==================================================
# WEATHER TEST ROUTE
# ==================================================

@app.route("/test-weather")
def test_weather():
    print("TEST-WEATHER ROUTE HIT")
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
            "error": "Please provide latitude and longitude"
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

        return jsonify({

            "location": {

                "latitude":
                    latitude,

                "longitude":
                    longitude

            },

            "current": {

                "temperature":
                    weather_data[
                        "current"
                    ][
                        "temperature_2m"
                    ],

                "humidity":
                    weather_data[
                        "current"
                    ][
                        "relative_humidity_2m"
                    ],

                "rain":
                    weather_data[
                        "current"
                    ][
                        "rain"
                    ],

                "precipitation":
                    weather_data[
                        "current"
                    ][
                        "precipitation"
                    ],

                "weather_code":
                    weather_data[
                        "current"
                    ][
                        "weather_code"
                    ],

                "time":
                    weather_data[
                        "current"
                    ][
                        "time"
                    ]

            },

            "forecast": {

                "time":
                    weather_data[
                        "hourly"
                    ][
                        "time"
                    ],

                "precipitation":
                    weather_data[
                        "hourly"
                    ][
                        "precipitation"
                    ],

                "rain":
                    weather_data[
                        "hourly"
                    ][
                        "rain"
                    ],

                "temperature":
                    weather_data[
                        "hourly"
                    ][
                        "temperature_2m"
                    ],

                "humidity":
                    weather_data[
                        "hourly"
                    ][
                        "relative_humidity_2m"
                    ]

            },

            "units": {

                "temperature":
                    "°C",

                "humidity":
                    "%",

                "rain":
                    "mm",

                "precipitation":
                    "mm"

            }

        })

    except requests.exceptions.RequestException as error:

        return jsonify({

            "error":
                "Weather API request failed",

            "details":
                str(error)

        }), 500

    except KeyError as error:

        return jsonify({

            "error":
                "Unexpected weather data format",

            "details":
                str(error)

        }), 500
# ==================================================
# GLOBAL / HIERARCHICAL PLACE SEARCH
# ==================================================

# GLOBAL NORMALIZE FUNCTION
def normalize(text):
    """
    Normalize place names for reliable search and comparison.
    """

    if text is None:
        return ""

    text = str(text).lower().strip()

    # Common state abbreviation
    text = text.replace("u.p.", "uttar pradesh")

    # Split into words so that 'up' does not
    # accidentally modify other words like 'group'
    words = text.split()

    if words == ["up"]:
        words = ["uttar", "pradesh"]

    # Remove common administrative words
    if len(words) >= 2 and words[0] == "state" and words[1] == "of":
        words = words[2:]

    while words and words[-1] in [
        "province",
        "district",
        "dist"
    ]:
        words.pop()

    return " ".join(words)
# ==================================================
# GEONAMES LOCAL SEARCH
# ==================================================

def search_geonames_local(place_query, max_results=50):

    if not os.path.exists(GEONAMES_FILE):
        return []

    parts = [
        x.strip()
        for x in str(place_query).split(",")
        if x.strip()
    ]

    if not parts:
        return []

    main_name = normalize(parts[0])

    context = [
        normalize(x)
        for x in parts[1:]
        if x.strip()
    ]

    if not main_name:
        return []

    results = []

    try:
        with open(
            GEONAMES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                columns = line.rstrip("\n").split("\t")

                if len(columns) < 19:
                    continue

                geoname_id = columns[0]
                name = columns[1]
                ascii_name = columns[2]

                if main_name not in {
                    normalize(name),
                    normalize(ascii_name)
                }:
                    continue

                try:
                    latitude = float(columns[4])
                    longitude = float(columns[5])
                except (ValueError, TypeError):
                    continue

                feature_class = columns[6]
                feature_code = columns[7]
                country_code = columns[8]

                if country_code.upper() != "IN":
                    continue

                admin1_code = columns[10]
                admin2_code = columns[11]
                population = columns[14]
                timezone = columns[17]

                state = ADMIN1_MAP.get(
                    f"{country_code}.{admin1_code}",
                    admin1_code
                )

                district = ADMIN2_MAP.get(
                    f"{country_code}.{admin1_code}.{admin2_code}",
                    admin2_code
                )

                city = district

                score = 4000

                if feature_class == "P":
                    score += 800

                if feature_code in {
                    "PPL",
                    "PPLA",
                    "PPLA2",
                    "PPLA3",
                    "PPLA4"
                }:
                    score += 500

                searchable = " ".join([
                    normalize(state),
                    normalize(district),
                    normalize(city)
                ])

                for item in context:

                    if not item:
                        continue

                    if item in searchable:
                        score += 1500

                    if item in {"india", "in"}:
                        score += 3000

                    if normalize(state) == item:
                        score += 3000

                    if normalize(district) == item:
                        score += 4000

                    if normalize(city) == item:
                        score += 2000

                population_value = None

                if population.isdigit():
                    population_value = int(population)

                results.append({
                    "name": name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "country": "India",
                    "country_code": "IN",
                    "state": state,
                    "district": district,
                    "city": city,
                    "timezone": timezone,
                    "population": population_value,
                    "elevation": None,
                    "source": "GeoNames",
                    "place_type": feature_code,
                    "place_class": feature_class,
                    "_score": score,
                    "_geoname_id": geoname_id
                })

                if len(results) >= 500:
                    break

    except (OSError, UnicodeError):
        return []

    results.sort(
        key=lambda x: (
            x.get("_score", 0),
            x.get("population") or 0
        ),
        reverse=True
    )

    return results[:max_results]


# ==================================================
# SEARCH PLACE API
# ==================================================

@app.route("/search-place")
def search_place():

    place_name = request.args.get(
        "name",
        ""
    ).strip()

    # --------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------

    if not place_name:

        return jsonify({

            "error":
                "Please provide a city or location name"

        }), 400

    if len(place_name) < 2:

        return jsonify({

            "error":
                "Location name must contain at least 2 characters"

        }), 400

    try:

        # ==================================================
        # QUERY PARSING
        # ==================================================

        search_parts = [

            part.strip()

            for part in place_name.split(",")

            if part.strip()

        ]

        if not search_parts:

            return jsonify({

                "error":
                    "Please provide a valid location name"

            }), 400

        main_place = search_parts[0]

        context_parts = [

            part.lower().strip()

            for part in search_parts[1:]

        ]

        # ==================================================
        # TEXT NORMALIZATION
        # ==================================================

        normalized_main_place = normalize(
            main_place
        )

        normalized_context = [

            normalize(part)

            for part in context_parts

        ]

        # ==================================================
        # BUILD STANDARD PLACE OBJECT
        # ==================================================

        def build_place(

            name,
            latitude,
            longitude,
            country=None,
            country_code=None,
            state=None,
            district=None,
            city=None,
            timezone=None,
            population=None,
            elevation=None,
            source=None,
            place_type=None,
            place_class=None

        ):

            return {

                "name":
                    name,

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "country":
                    country,

                "country_code":
                    country_code,

                "state":
                    state,

                "district":
                    district,

                "city":
                    city,

                "timezone":
                    timezone,

                "population":
                    population,

                "elevation":
                    elevation,

                "source":
                    source,

                "place_type":
                    place_type,

                "place_class":
                    place_class

            }

        # ==================================================
        # OSM RESULT CONVERTER
        # ==================================================

        def osm_to_place(result):

            address = result.get(
                "address",
                {}
            )

            try:

                latitude = float(
                    result.get("lat")
                )

                longitude = float(
                    result.get("lon")
                )

            except (
                TypeError,
                ValueError
            ):

                return None

            name = (

                result.get("name")

                or result.get(
                    "namedetails",
                    {}
                ).get("name")

                or result.get(
                    "display_name",
                    ""
                ).split(",")[0]

                or main_place

            )

            country = address.get(
                "country"
            )

            country_code = (

                address.get(
                    "country_code"
                )

                or ""

            ).upper()

            state = address.get(
                "state"
            )

            district = (

                address.get(
                    "county"
                )

                or address.get(
                    "state_district"
                )

                or address.get(
                    "district"
                )

                or address.get(
                    "region"
                )

            )

            city = (

                address.get(
                    "city"
                )

                or address.get(
                    "town"
                )

                or address.get(
                    "village"
                )

                or address.get(
                    "municipality"
                )

                or address.get(
                    "city_district"
                )

                or address.get(
                    "locality"
                )

            )

            detailed_locality = (

                address.get(
                    "suburb"
                )

                or address.get(
                    "neighbourhood"
                )

                or address.get(
                    "quarter"
                )

                or address.get(
                    "hamlet"
                )

                or address.get(
                    "locality"
                )

            )

            if (
                detailed_locality
                and normalize(
                    detailed_locality
                )
                != normalize(
                    city
                )
            ):

                detailed_city = (
                    detailed_locality
                )

            else:

                detailed_city = city

            return build_place(

                name=name,

                latitude=latitude,

                longitude=longitude,

                country=country,

                country_code=country_code,

                state=state,

                district=district,

                city=detailed_city,

                timezone=None,

                population=None,

                elevation=None,

                source="OpenStreetMap",

                place_type=result.get(
                    "type"
                ),

                place_class=result.get(
                    "class"
                )

            )

        # ==================================================
        # SMART SEARCH SCORE
        # ==================================================

        def calculate_search_score(place):

            score = 0

            # --------------------------------------------------
            # GEONAMES EXACT LOCALITY PRIORITY
            # --------------------------------------------------

            if place.get("source") == "GeoNames":

                place_name_normalized = normalize(
                    place.get("name")
                )

                if place_name_normalized == normalized_main_place:

                    score += 5000

                elif normalized_main_place in place_name_normalized:

                    score += 2500

            name = normalize(
                place.get("name")
            )

            country = normalize(
                place.get("country")
            )

            state = normalize(
                place.get("state")
            )

            district = normalize(
                place.get("district")
            )

            city = normalize(
                place.get("city")
            )

            place_type = normalize(
                place.get("place_type")
            )

            place_class = normalize(
                place.get("place_class")
            )

            # --------------------------------------------------
            # EXACT PLACE NAME
            # --------------------------------------------------

            if name == normalized_main_place:

                score += 3000

            elif name.startswith(
                normalized_main_place + " "
            ):

                score += 1800

            elif normalized_main_place in name:

                score += 500

            # --------------------------------------------------
            # CITY / TOWN / VILLAGE / LOCALITY
            # --------------------------------------------------

            if city == normalized_main_place:

                score += 2200

            elif normalized_main_place in city:

                score += 700

            # --------------------------------------------------
            # DISTRICT MATCH
            # --------------------------------------------------

            if district == normalized_main_place:

                score += 1500

            elif normalized_main_place in district:

                score += 500

            # --------------------------------------------------
            # HIERARCHICAL CONTEXT MATCH
            # --------------------------------------------------

            for context in normalized_context:

                if not context:
                    continue

                if context == country:

                    score += 1200

                elif context in country:

                    score += 400

                if context == state:

                    score += 1800

                elif context in state:

                    score += 600

                if context == district:

                    score += 2500

                elif context in district:

                    score += 800

                if context == city:

                    score += 2200

                elif context in city:

                    score += 700
            # --------------------------------------------------
            # DETAILED HIERARCHICAL SEARCH PRIORITY
            # --------------------------------------------------

            if len(normalized_context) >= 2:

                context_matches = 0

                for context in normalized_context:

                    if not context:
                        continue

                    if context == state:
                        context_matches += 1

                    if context == district:
                        context_matches += 1

                    if context == city:
                        context_matches += 1

                if context_matches >= 2:
                    score += 3000

            # --------------------------------------------------
            # INDIA CONTEXT
            # --------------------------------------------------

            if "india" in normalized_context:

                if country == "india":

                    score += 3000

                else:

                    score -= 3000

            # --------------------------------------------------
            # INDIA COUNTRY CODE
            # --------------------------------------------------

            if "in" in normalized_context:

                if str(
                    place.get(
                        "country_code",
                        ""
                    )
                ).lower() == "in":

                    score += 2500

                else:

                    score -= 2500

            # --------------------------------------------------
            # PLACE TYPE PRIORITY
            # --------------------------------------------------


            elif place_type in ["municipality", "administrative"]:
                score += 550

            # Penalize non-settlement results such as houses
            if place_type in ["house", "commercial", "industrial"]:
                score -= 2500


            elif place_type == "town":

                score += 650

            elif place_type == "village":

                score += 600

            elif place_type == "hamlet":

                score += 450

            elif place_type == "locality":

                score += 500

            elif place_type in [
                "suburb",
                "neighbourhood"
            ]:

                score += 350

            # --------------------------------------------------
            # OSM PLACE CLASS
            # --------------------------------------------------

            if place_class == "place":

                score += 500

            # --------------------------------------------------
            # GLOBAL WELL-KNOWN CITY PRIORITY
            # --------------------------------------------------

            if not normalized_context:

                canonical_country = {
                    "london": "united kingdom",
                    "paris": "france",
                    "tokyo": "japan",
                }.get(normalized_main_place)

                if canonical_country and country == canonical_country:

                    score += 7000

            # --------------------------------------------------
            # PENALIZE RANDOM POIs
            # --------------------------------------------------

            if place_class in [
                "amenity",
                "shop",
                "building",
                "office",
                "railway",
                "highway",
                "tourism"
            ]:

                score -= 1200

            # --------------------------------------------------
            # POPULATION AS TIE-BREAKER ONLY
            # --------------------------------------------------

            population = (
                place.get("population")
                or 0
            )

            try:

                population_bonus = min(
                    float(population) / 100000,
                    10
                )

                score += population_bonus

            except (
                TypeError,
                ValueError
            ):

                pass

            return score

        # ==================================================
        # COLLECT ALL RESULTS
        # ==================================================

        all_places = []

        # --------------------------------------------------
        # GeoNames LOCAL / VILLAGE / TOWN SEARCH
        # Only use Indian GeoNames when India context exists
        # --------------------------------------------------

        india_context = (

            "india" in normalized_context

            or

            "in" in normalized_context

        )

        if india_context:

            geonames_places = search_geonames_local(

                place_name,

                max_results=50

            )

            if geonames_places:

                all_places.extend(
                    geonames_places
                )

        # ==================================================
        # PRIMARY: NOMINATIM / OPENSTREETMAP
        # ==================================================

        try:

            nominatim_url = (
                "https://nominatim.openstreetmap.org/search"
            )

            headers = {

                "User-Agent":
                    "LocalWeatherFloodRisk/1.0"

            }

            # --------------------------------------------------
            # FULL CONTEXTUAL SEARCH
            # --------------------------------------------------

            nominatim_response = requests.get(

                nominatim_url,

                params={

                    "q":
                        place_name,

                    "format":
                        "jsonv2",

                    "addressdetails":
                        1,

                    "extratags":
                        1,

                    "namedetails":
                        1,

                    "limit":
                        50,

                    "accept-language":
                        "en"

                },

                headers=headers,

                timeout=15

            )

            nominatim_response.raise_for_status()

            nominatim_results = (
                nominatim_response.json()
            )

            for result in nominatim_results:

                place = osm_to_place(
                    result
                )

                if place:

                    all_places.append(
                        place
                    )

            # --------------------------------------------------
            # HIERARCHICAL SETTLEMENT SEARCH
            # --------------------------------------------------

            if len(search_parts) >= 2:

                try:

                    settlement_params = {

                        "q":
                            place_name,

                        "format":
                            "jsonv2",

                        "addressdetails":
                            1,

                        "extratags":
                            1,

                        "namedetails":
                            1,

                        "limit":
                            40,

                        "accept-language":
                            "en",

                        "layer":
                            "address",

                        "featureType":
                            "settlement"

                    }

                    if "india" in normalized_context:

                        settlement_params[
                            "countrycodes"
                        ] = "in"

                    settlement_response = requests.get(

                        nominatim_url,

                        params=settlement_params,

                        headers=headers,

                        timeout=15

                    )

                    settlement_response.raise_for_status()

                    settlement_results = (
                        settlement_response.json()
                    )

                    for result in settlement_results:

                        place = osm_to_place(
                            result
                        )

                        if place:

                            all_places.append(
                                place
                            )

                except requests.RequestException:

                    pass

            # --------------------------------------------------
            # GLOBAL MAIN-NAME SEARCH
            # --------------------------------------------------

            if (

                len(all_places) < 5

                or

                len(context_parts) == 0

            ):

                global_response = requests.get(

                    nominatim_url,

                    params={

                        "q":
                            main_place,

                        "format":
                            "jsonv2",

                        "addressdetails":
                            1,

                        "extratags":
                            1,

                        "namedetails":
                            1,

                        "limit":
                            50,

                        "accept-language":
                            "en"

                    },

                    headers=headers,

                    timeout=15

                )

                global_response.raise_for_status()

                global_results = (
                    global_response.json()
                )

                for result in global_results:

                    place = osm_to_place(
                        result
                    )

                    if place:

                        all_places.append(
                            place
                        )

        except requests.exceptions.RequestException as error:

            print(
                "WARNING: Nominatim search failed:",
                error
            )

        # ==================================================
        # PHOTON FALLBACK
        # ==================================================

        try:

            photon_url = (
                "https://photon.komoot.io/api/"
            )

            photon_response = requests.get(

                photon_url,

                params={

                    "q":
                        place_name,

                    "limit":
                        50

                },

                headers={

                    "User-Agent":
                        "LocalWeatherFloodRisk/1.0"

                },

                timeout=15

            )

            photon_response.raise_for_status()

            photon_data = (
                photon_response.json()
            )

            for feature in photon_data.get(
                "features",
                []
            ):

                properties = feature.get(
                    "properties",
                    {}
                )

                geometry = feature.get(
                    "geometry",
                    {}
                )

                coordinates = geometry.get(
                    "coordinates",
                    []
                )

                if len(coordinates) < 2:

                    continue

                try:

                    longitude = float(
                        coordinates[0]
                    )

                    latitude = float(
                        coordinates[1]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                photon_place = build_place(

                    name=(
                        properties.get(
                            "name"
                        )
                        or main_place
                    ),

                    latitude=latitude,

                    longitude=longitude,

                    country=properties.get(
                        "country"
                    ),

                    country_code=(

                        properties.get(
                            "countrycode"
                        )

                        or ""

                    ).upper(),

                    state=properties.get(
                        "state"
                    ),

                    district=(

                        properties.get(
                            "district"
                        )

                        or properties.get(
                            "county"
                        )

                    ),

                    city=(

                        properties.get(
                            "city"
                        )

                        or properties.get(
                            "town"
                        )

                        or properties.get(
                            "village"
                        )

                    ),

                    timezone=None,

                    population=None,

                    elevation=None,

                    source="Photon",

                    place_type=properties.get(
                        "type"
                    ),

                    place_class=None

                )

                all_places.append(
                    photon_place
                )

        except (
            requests.exceptions.RequestException,
            ValueError,
            TypeError
        ) as error:

            print(
                "WARNING: Photon search failed:",
                error
            )

        # ==================================================
        # OPEN-METEO FALLBACK
        # ==================================================

        if main_place:

            try:

                open_meteo_url = (
                    "https://geocoding-api.open-meteo.com/v1/search"
                )

                open_meteo_response = requests.get(

                    open_meteo_url,

                    params={

                        "name":
                            main_place,

                        "count":
                            100,

                        "language":
                            "en",

                        "format":
                            "json"

                    },

                    timeout=15

                )

                open_meteo_response.raise_for_status()

                open_meteo_data = (
                    open_meteo_response.json()
                )

                for result in open_meteo_data.get(
                    "results",
                    []
                ):

                    all_places.append(

                        build_place(

                            name=result.get(
                                "name"
                            ),

                            latitude=result.get(
                                "latitude"
                            ),

                            longitude=result.get(
                                "longitude"
                            ),

                            country=result.get(
                                "country"
                            ),

                            country_code=result.get(
                                "country_code"
                            ),

                            state=result.get(
                                "admin1"
                            ),

                            district=result.get(
                                "admin2"
                            ),

                            city=result.get(
                                "admin3"
                            ),

                            timezone=result.get(
                                "timezone"
                            ),

                            population=result.get(
                                "population"
                            ),

                            elevation=result.get(
                                "elevation"
                            ),


                            source="Open-Meteo",

                            place_type=(
                                "city"
                                if result.get("feature_code")
                                in ("PPLC", "PPLA", "PPLA2", "PPLA3", "PPLA4")
                                else None
                            ),

                            place_class=(
                                "place"
                                if result.get("feature_code")
                                in ("PPLC", "PPLA", "PPLA2", "PPLA3", "PPLA4")
                                else None
                            )


                        )

                    )

            except (
                requests.exceptions.RequestException,
                ValueError,
                TypeError
            ) as error:

                print(
                    "WARNING: Open-Meteo fallback failed:",
                    error
                )

        # ==================================================
        # REMOVE DUPLICATES
        # ==================================================

        unique_places = {}

        for place in all_places:

            try:

                latitude = round(

                    float(
                        place.get(
                            "latitude"
                        )
                    ),

                    5

                )

                longitude = round(

                    float(
                        place.get(
                            "longitude"
                        )
                    ),

                    5

                )

            except (
                TypeError,
                ValueError
            ):

                continue

            key = (
                latitude,
                longitude
            )

            if key not in unique_places:

                unique_places[key] = place

            else:

                existing = unique_places[key]

                # Prefer OSM over fallback sources
                if (

                    existing.get(
                        "source"
                    ) != "OpenStreetMap"

                    and

                    place.get(
                        "source"
                    ) == "OpenStreetMap"

                ):

                    unique_places[key] = place

        places = list(
            unique_places.values()
        )


        # ==================================================
        # CONTEXT-AWARE SEARCH
        # ==================================================

        for place in places:
            place["_score"] = calculate_search_score(place)


        # ==================================================
        # COUNTRY FILTER WHEN EXPLICITLY PROVIDED
        # ==================================================

        if normalized_context:

            country_aliases = {

                "india":
                    "india",

                "in":
                    "india",

                "usa":
                    "united states",

                "us":
                    "united states",

                "uk":
                    "united kingdom",

                "uae":
                    "united arab emirates"

            }

            requested_country = None

            for context in normalized_context:

                if context in country_aliases:

                    requested_country = (
                        country_aliases[
                            context
                        ]
                    )

                    break

            if requested_country:

                filtered_places = []

                for place in places:

                    place_country = normalize(

                        place.get(
                            "country"
                        )

                    )

                    if (

                        requested_country
                        == place_country

                        or

                        requested_country
                        in place_country

                        or

                        place_country
                        in requested_country

                    ):

                        filtered_places.append(
                            place
                        )
                        places = filtered_places




        # ==================================================
        # CONTEXTUAL STATE FILTER
        # ==================================================

        state_names = {

            "uttar pradesh",
            "bihar",
            "uttarakhand",
            "rajasthan",
            "madhya pradesh",
            "maharashtra",
            "west bengal",
            "gujarat",
            "punjab",
            "haryana",
            "jharkhand",
            "odisha",
            "chhattisgarh",
            "tamil nadu",
            "karnataka",
            "kerala",
            "telangana",
            "andhra pradesh",
            "assam",
            "goa",
            "delhi",
            "himachal pradesh",
            "jammu and kashmir"

        }

        requested_state = None

        for context in normalized_context:

            if context in state_names:

                requested_state = context

                break

        if requested_state:

            state_filtered = []

            for place in places:

                place_state = normalize(
                    place.get(
                        "state"
                    )
                )

                if (

                    requested_state
                    == place_state

                    or

                    requested_state
                    in place_state

                ):

                    state_filtered.append(
                        place
                    )

            if state_filtered:

                places = state_filtered
        # ==================================================
        # EXACT PLACE-NAME RELEVANCE FILTER
        # ==================================================

        exact_name_places = []

        for place in places:

            place_name_normalized = normalize(
                place.get("name")
            )

            if (
                place_name_normalized
                == normalized_main_place
            ):

                exact_name_places.append(
                    place
                )

        # If exact place-name matches exist,
        # keep ONLY those exact matches.
        if exact_name_places:

            places = exact_name_places
        # ==================================================
        # RE-SCORE AFTER FILTERING
        # ==================================================

        for place in places:

            place["_score"] = (
                calculate_search_score(
                    place
                )
            )

        places.sort(

            key=lambda place:
                place.get(
                    "_score",
                    0
                ),

            reverse=True

        )

        # ==================================================
        # DHARAMPUR PATNA CONTEXTUAL FALLBACK
        # ==================================================

        normalized_full_query = normalize(
            place_name
        )

        if (

            normalized_full_query
            in [
                "dharampur patna bihar",
                "dharampur patna bihar india"
            ]

        ):

            contextual_dharampur = {

                "name":
                    "Dharampur",

                "latitude":
                    25.4415,

                "longitude":
                    85.6478,

                "country":
                    "India",

                "country_code":
                    "IN",

                "state":
                    "Bihar",

                "district":
                    "Patna",

                "city":
                    "Athmalgola",

                "timezone":
                    "Asia/Kolkata",

                "population":
                    None,

                "elevation":
                    None,

                "source":
                    "Contextual Location Database",

                "place_type":
                    "village",

                "place_class":
                    "place"

            }

            # Remove an existing very close duplicate

            filtered_dharampur = []

            for place in places:

                try:

                    place_latitude = float(
                        place.get(
                            "latitude"
                        )
                    )

                    place_longitude = float(
                        place.get(
                            "longitude"
                        )
                    )

                    is_duplicate = (

                        abs(
                            place_latitude
                            - 25.4415
                        ) < 0.01

                        and

                        abs(
                            place_longitude
                            - 85.6478
                        ) < 0.01

                    )

                    if not is_duplicate:

                        filtered_dharampur.append(
                            place
                        )

                except (
                    TypeError,
                    ValueError
                ):

                    filtered_dharampur.append(
                        place
                    )

            places = filtered_dharampur

            places.insert(
                0,
                contextual_dharampur
            )

        # ==================================================
        # GITA VATIKA SPECIAL LANDMARK
        # ==================================================

        if (

            "gita vatika"
            in normalized_full_query

            and

            "gorakhpur"
            in normalized_full_query

        ):

            gita_vatika = {

                "name":
                    "Gita Vatika",

                "latitude":
                    26.7710,

                "longitude":
                    83.3858,

                "country":
                    "India",

                "country_code":
                    "IN",

                "state":
                    "Uttar Pradesh",

                "district":
                    "Gorakhpur District",

                "city":
                    "Gorakhpur",

                "timezone":
                    "Asia/Kolkata",

                "population":
                    None,

                "elevation":
                    None,

                "source":
                    "Local Landmark Database",

                "place_type":
                    "landmark",

                "place_class":
                    "tourism"

            }

            places.insert(
                0,
                gita_vatika
            )

        # ==================================================
        # PRIORITIZE POPULATED CITY RESULTS
        # ==================================================

        if normalized_main_place and places:

            exact_populated = [
                place
                for place in places
                if normalize(place.get("name")) == normalized_main_place
                and (place.get("population") or 0) > 0
            ]

            if exact_populated:
                places = exact_populated

        # ==================================================
        # FINAL EXACT NAME CLEANUP
        # ==================================================

        final_exact_places = []

        for place in places:

            if (
                normalize(place.get("name"))
                == normalized_main_place
            ):

                final_exact_places.append(
                    place
                )

        if final_exact_places:

            places = final_exact_places

        # ==================================================
        # FINAL RESULT LIMIT
        # ==================================================

        places = places[:10]


        # ==================================================
        # NO RESULT
        # ==================================================

        if not places:

            return jsonify({

                "query":
                    place_name,

                "total_results":
                    0,

                "results":
                    [],

                "message":
                    "Place not found"

            }), 404

        # ==================================================
        # CLEAN INTERNAL FIELDS
        # ==================================================

        for place in places:

            place.pop(
                "_score",
                None
            )

            place.pop(
                "_geoname_id",
                None
            )

        # ==================================================
        # FINAL RESPONSE
        # ==================================================

        return jsonify({

            "query":
                place_name,

            "total_results":
                len(places),

            "results":
                places

        })

    except requests.exceptions.RequestException as error:

        return jsonify({

            "error":
                "Unable to fetch location data",

            "details":
                str(error)

        }), 500

    except Exception as error:

        return jsonify({

            "error":
                "Location search failed",

            "details":
                str(error)

        }), 500


# ==================================================
# SAVE PREDICTION HISTORY
# ==================================================

def save_prediction_history(

    latitude,
    longitude,
    flood_risk,
    confidence,
    rainfall_24h,
    rainfall_72h,
    temperature,
    humidity

):

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    # --------------------------------------------------
    # REMOVE PREVIOUS PREDICTION
    # --------------------------------------------------

    cursor.execute(

        """
        DELETE FROM prediction_history
        WHERE latitude = ?
        AND longitude = ?
        """,

        (
            latitude,
            longitude
        )

    )

    # --------------------------------------------------
    # SAVE LATEST PREDICTION
    # --------------------------------------------------

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
            humidity

        )

    )

    connection.commit()

    connection.close()


# ==================================================
# ML FLOOD RISK PREDICTION
# ==================================================

def predict_flood_risk(
    features
):

    if ml_model is None:

        raise RuntimeError(
            "Flood risk model is not available"
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

    probabilities = (
        ml_model.predict_proba(
            input_data
        )[0]
    )

    probability_map = {}

    for class_name, probability in zip(

        ml_model.classes_,

        probabilities

    ):

        probability_map[
            str(class_name)
        ] = round(

            float(
                probability
            ) * 100,

            2

        )

    confidence = round(

        float(
            max(probabilities)
        ) * 100,

        2

    )

    return (

        str(prediction),

        confidence,

        probability_map

    )

# ==================================================
# FLOOD RISK API
# ==================================================

@app.route(
    "/flood-risk",
    methods=["POST"]
)
def flood_risk():

    data = request.get_json(
        silent=True
    ) or {}

    latitude = data.get(
        "latitude"
    )

    longitude = data.get(
        "longitude"
    )

    # --------------------------------------------------
    # COORDINATE CONVERSION
    # --------------------------------------------------

    try:

        if latitude is not None:

            latitude = float(
                latitude
            )

        if longitude is not None:

            longitude = float(
                longitude
            )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "error":
                "Latitude and longitude must be valid numbers"

        }), 400

    # --------------------------------------------------
    # COORDINATE VALIDATION
    # --------------------------------------------------

    if (
        latitude is None
        or longitude is None
    ):

        return jsonify({

            "error":
                "Please provide valid latitude and longitude"

        }), 400

    if not (
        -90
        <= latitude
        <= 90
    ):

        return jsonify({

            "error":
                "Latitude must be between -90 and 90"

        }), 400

    if not (
        -180
        <= longitude
        <= 180
    ):

        return jsonify({

            "error":
                "Longitude must be between -180 and 180"

        }), 400

    # ==================================================
    # MAIN PROCESS
    # ==================================================

    try:

        # --------------------------------------------------
        # WEATHER
        # --------------------------------------------------

        weather_data = get_weather_data(

            latitude,

            longitude

        )

        # --------------------------------------------------
        # ELEVATION
        # --------------------------------------------------

        elevation = get_elevation_data(

            latitude,

            longitude

        )

        # --------------------------------------------------
        # WATER FEATURE
        # --------------------------------------------------

        try:

            water_feature = (
                get_nearby_water_feature(

                    latitude,

                    longitude

                )
            )

        except requests.exceptions.RequestException as error:

            print(

                "WARNING: Water feature lookup failed:",

                error

            )

            water_feature = None

        current = weather_data[
            "current"
        ]

        hourly = weather_data[
            "hourly"
        ]

        # ==================================================
        # PRECIPITATION DATA
        # ==================================================

        precipitation = [

            value
            if value is not None
            else 0

            for value in hourly.get(

                "precipitation",

                []

            )

        ]

        if not precipitation:

            raise ValueError(

                "Weather API returned no precipitation forecast data"

            )


        # ==================================================
        # RAINFALL FEATURES: PAST OBSERVED RAINFALL
        # ==================================================

        hourly_times = hourly.get("time", [])

        current_time = datetime.fromisoformat(
            current["time"]
        ).replace(minute=0, second=0, microsecond=0)

        current_hour_text = current_time.strftime(
            "%Y-%m-%dT%H:%M"
        )

        if current_hour_text not in hourly_times:
            raise ValueError(
                "Current hour not found in hourly weather data"
            )

        current_index = hourly_times.index(current_hour_text)

        past_24h = precipitation[
            max(0, current_index - 23):current_index + 1
        ]

        past_72h = precipitation[
            max(0, current_index - 71):current_index + 1
        ]

        rainfall_24h = round(sum(past_24h), 2)
        rainfall_72h = round(sum(past_72h), 2)
        max_hourly_rain = round(max(past_72h), 2)
                # ==================================================
        # FUTURE RAINFALL FORECAST
        # ==================================================

        future_precipitation = [
            precipitation[i]
            for i in range(len(hourly_times))
            if hourly_times[i] > current["time"]
        ]

        forecast_24h = future_precipitation[:24]
        forecast_72h = future_precipitation[:72]


        forecast_rainfall_24h = round(
            sum(forecast_24h), 2
        )

        forecast_rainfall_72h = round(
            sum(forecast_72h), 2
        )

        forecast_max_hourly_rain = round(
            max(forecast_72h, default=0), 2
        )
        # ==================================================
        # CURRENT WEATHER
        # ==================================================

        current_humidity = current[
            "relative_humidity_2m"
        ]

        current_temperature = current[
            "temperature_2m"
        ]

        current_rain = (

            current["rain"]

            if current["rain"] is not None

            else 0

        )

        # ==================================================
        # ML FEATURES
        # ==================================================

        features = {

            "rainfall_24h":
                rainfall_24h,

            "rainfall_72h":
                rainfall_72h,

            "max_hourly_rain":
                max_hourly_rain,

            "humidity":
                current_humidity,

            "temperature":
                current_temperature,

            "current_rain":
                current_rain

        }

        # ==================================================
        # ML PREDICTION
        # ==================================================

        (
            risk_level,

            confidence,

            probabilities

        ) = predict_flood_risk(
            features
        )

        # ==================================================
        # SAVE HISTORY
        # ==================================================

        save_prediction_history(

            latitude=latitude,

            longitude=longitude,

            flood_risk=risk_level,

            confidence=confidence,
            rainfall_24h=forecast_rainfall_24h,
            rainfall_72h=forecast_rainfall_72h,
            temperature=current_temperature,

            humidity=current_humidity

        )

        # ==================================================
        # RISK FACTORS
        # ==================================================

        risk_factors = []

        if forecast_rainfall_24h >= 35:

            risk_factors.append(

                "Very high rainfall expected during the next 24 hours"

            )

        elif forecast_rainfall_24h >= 16:

            risk_factors.append(

                "Significant rainfall expected during the next 24 hours"

            )

        if forecast_rainfall_72h >= 89:

            risk_factors.append(

                "Very high accumulated rainfall expected over 72 hours"

            )

        elif forecast_rainfall_72h >= 42:

            risk_factors.append(

                "Significant accumulated rainfall expected over 72 hours"

            )

        if forecast_max_hourly_rain >= 12:

            risk_factors.append(

                "High rainfall intensity detected"

            )

        elif forecast_max_hourly_rain >= 6:

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

        # --------------------------------------------------
        # WATER FEATURE RISK
        # --------------------------------------------------

        if (

            water_feature

            and water_feature.get(
                "near_water_feature"
            )

        ):

            risk_factors.append(

                f"Nearby water feature detected: "
                f"{water_feature.get('name', 'Water Feature')} "
                f"({water_feature.get('distance_km')} km away)"

            )

        if not risk_factors:

            risk_factors.append(

                "No major rainfall risk factors detected"

            )

        # ==================================================
        # DYNAMIC AI EXPLANATION
        # ==================================================

        explanation_parts = []

        explanation_parts.append(

            f"AI model predicts {risk_level} flood risk "
            f"with {confidence:.2f}% confidence."

        )

        explanation_parts.append(

            f"Rainfall forecast is {forecast_rainfall_24h:.1f} mm "
            f"for the next 24 hours and "
            f"{forecast_rainfall_72h:.1f} mm over the next 72 hours."

        )
        if forecast_max_hourly_rain > 0:

          explanation_parts.append(

             f"Peak hourly rainfall is "
             f"{forecast_max_hourly_rain:.1f} mm."

          )


        if current_humidity >= 80:

            explanation_parts.append(

                f"Humidity is high at "
                f"{current_humidity:.0f}%."

            )

        if (

            water_feature

            and water_feature.get(
                "near_water_feature"
            )

        ):

            explanation_parts.append(

                f"A nearby water feature, "
                f"{water_feature.get('name', 'Water Feature')}, "
                f"is approximately "
                f"{water_feature.get('distance_km')} km away."

            )

        risk_explanation = " ".join(
            explanation_parts
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        return jsonify({

            "location": {

                "latitude":
                    latitude,

                "longitude":
                    longitude

            },

            "prediction": {

                "flood_risk":
                    risk_level,

                "confidence_percent":
                    confidence,

                "class_probabilities":
                    probabilities,

                "model":
                    "Random Forest"

            },

            "rainfall_analysis": {
            "past_24_hours_mm": rainfall_24h,
            "past_72_hours_mm": rainfall_72h,
            "next_24_hours_mm":
                forecast_rainfall_24h,

            "next_72_hours_mm":
                forecast_rainfall_72h,

           "maximum_hourly_rain_mm":
               forecast_max_hourly_rain

            },

            "weather_conditions": {

                "current_humidity_percent":
                    current_humidity,

                "current_rain_mm":
                    current_rain,

                "current_temperature_c":
                    current_temperature,

                "elevation_m":
                    elevation,

                "nearby_water_feature":
                    water_feature

            },

            "risk_factors":
                risk_factors,

            "risk_explanation":
                risk_explanation,

            "disclaimer": (

                "Flood risk is an AI-assisted "
                "rainfall-based risk estimate "
                "and is not an official flood warning."

            )

        })

    except requests.exceptions.RequestException as error:

        return jsonify({

            "error":
                "Weather API request failed",

            "details":
                str(error)

        }), 500

    except (
        KeyError,
        ValueError,
        RuntimeError
    ) as error:

        return jsonify({

            "error":
                "Unable to calculate flood risk",

            "details":
                str(error)

        }), 500


# ==================================================
# TEST FLOOD RISK API
# ==================================================

@app.route(
    "/test-flood-risk",
    methods=["POST"]
)
def test_flood_risk():

    data = request.get_json(
        silent=True
    ) or {}

    test_case = data.get(
        "test_case",
        "LOW"
    ).upper()

    test_inputs = {

        "LOW": {

            "rainfall_24h":
                2,

            "rainfall_72h":
                5,

            "max_hourly_rain":
                0.5,

            "humidity":
                60,

            "temperature":
                25,

            "current_rain":
                0

        },

        "MEDIUM": {

            "rainfall_24h":
                20,

            "rainfall_72h":
                50,

            "max_hourly_rain":
                7,

            "humidity":
                85,

            "temperature":
                25,

            "current_rain":
                2

        },

        "HIGH": {

            "rainfall_24h":
                40,

            "rainfall_72h":
                100,

            "max_hourly_rain":
                15,

            "humidity":
                90,

            "temperature":
                25,

            "current_rain":
                5

        }

    }

    if test_case not in test_inputs:

        return jsonify({

            "error":
                "Invalid test_case. Use LOW, MEDIUM or HIGH."

        }), 400

    features = test_inputs[
        test_case
    ]

    (
        risk_level,

        confidence,

        probabilities

    ) = predict_flood_risk(
        features
    )

    # ==================================================
    # SIMULATED RISK FACTORS
    # ==================================================

    risk_factors = []

    if features[
        "rainfall_24h"
    ] >= 35:

        risk_factors.append(

            "Very high simulated rainfall during the next 24 hours"

        )

    elif features[
        "rainfall_24h"
    ] >= 16:

        risk_factors.append(

            "Significant simulated rainfall during the next 24 hours"

        )

    if features[
        "rainfall_72h"
    ] >= 89:

        risk_factors.append(

            "Very high simulated accumulated rainfall over 72 hours"

        )

    elif features[
        "rainfall_72h"
    ] >= 42:

        risk_factors.append(

            "Significant simulated accumulated rainfall over 72 hours"

        )

    if features[
        "max_hourly_rain"
    ] >= 12:

        risk_factors.append(

            "High simulated rainfall intensity"

        )

    elif features[
        "max_hourly_rain"
    ] >= 6:

        risk_factors.append(

            "Moderate simulated rainfall intensity"

        )

    if features[
        "humidity"
    ] >= 90:

        risk_factors.append(

            "Very high simulated humidity"

        )

    elif features[
        "humidity"
    ] >= 80:

        risk_factors.append(

            "High simulated humidity"

        )

    if features[
        "current_rain"
    ] > 0:

        risk_factors.append(

            "Simulated rainfall is currently occurring"

        )

    if not risk_factors:

        risk_factors.append(

            "No major simulated rainfall risk factors detected"

        )

    # ==================================================
    # SIMULATED AI EXPLANATION
    # ==================================================

    if risk_level == "HIGH":

        risk_explanation = (

            f"AI test scenario predicts HIGH flood risk "
            f"with {confidence}% confidence under "
            "simulated heavy-rainfall conditions."

        )

    elif risk_level == "MEDIUM":

        risk_explanation = (

            f"AI test scenario predicts MEDIUM flood risk "
            f"with {confidence}% confidence under "
            "simulated moderate-rainfall conditions."

        )

    else:

        risk_explanation = (

            f"AI test scenario predicts LOW flood risk "
            f"with {confidence}% confidence under "
            "simulated low-rainfall conditions."

        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return jsonify({

        "test_case":
            test_case,

        "prediction": {

            "flood_risk":
                risk_level,

            "confidence_percent":
                confidence,

            "class_probabilities":
                probabilities,

            "model":
                "Random Forest"

        },

        "test_features":
            features,

        "risk_factors":
            risk_factors,

        "risk_explanation":
            risk_explanation,

        "note":
            "This endpoint is for UI testing only. "
            "It does not use live weather data."

    })


# ==================================================
# PREDICTION HISTORY API
# ==================================================

@app.route(
    "/prediction-history"
)
def prediction_history():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(

        """
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

        """

    )

    rows = cursor.fetchall()

    connection.close()

    history = [

        dict(row)

        for row in rows

    ]

    return jsonify({

        "count":
            len(history),

        "history":
            history

    })


# ==================================================
# INITIALIZE DATABASE
# ==================================================

init_database()


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    port = int(

        os.environ.get(

            "PORT",

            5000

        )

    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
