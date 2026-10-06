import jsPDF from "jspdf";
import { useState } from "react";
import {
  AlertTriangle,
  CloudRain,
  Droplets,
  LoaderCircle,
  MapPin,
  Navigation,
  Search,
  ShieldAlert,
  Thermometer,
  Waves,
  Wind,
} from "lucide-react";

import {
 Bar,
BarChart,
CartesianGrid,
Line,
LineChart,
ResponsiveContainer,
Scatter,
ScatterChart,
Tooltip,
XAxis,
YAxis, 
} from "recharts";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "./App.css";
const DefaultIcon = L.icon({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

// --------------------------------------------------
// MAP UPDATER
// --------------------------------------------------

function MapUpdater({ latitude, longitude }) {
  const map = useMap();

  map.setView(
    [Number(latitude), Number(longitude)],
    11
  );

  return null;
}


// --------------------------------------------------
// MAIN APP
// --------------------------------------------------

function App() {
  const [latitude, setLatitude] = useState("26.8467");
  const [longitude, setLongitude] = useState("80.9462");

  const [city, setCity] = useState("");
  const [locationResults, setLocationResults] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState("");
  const [searchingLocation, setSearchingLocation] = useState(false);

  const [weatherData, setWeatherData] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [forecastData, setForecastData] = useState(null);

  const [loading, setLoading] = useState(false);

  const [testMode, setTestMode] = useState(false);
  const [testPrediction, setTestPrediction] = useState(null);
  const [earlyWarning, setEarlyWarning] = useState(null);
const [error, setError] = useState("");
  const generateEarlyWarning = (prediction) => {
    if (!prediction) {
      setEarlyWarning(null);
      return;
    }

    const risk = String(
      prediction.flood_risk || ""
    ).toUpperCase();

    if (risk === "HIGH") {
      setEarlyWarning({
        level: "HIGH",
        title: "Flood Early Warning",
        message:
          "High rainfall-based flood risk detected. Immediate monitoring and precautionary action are recommended.",
      });
    } else if (risk === "MEDIUM") {
      setEarlyWarning({
        level: "MEDIUM",
        title: "Flood Risk Advisory",
        message:
          "Moderate rainfall-based flood risk detected. Continue monitoring weather and rainfall conditions.",
      });
    } else {
      setEarlyWarning({
        level: "LOW",
        title: "Low Flood Risk",
        message:
          "Current rainfall-based conditions indicate relatively low flood risk.",
      });
    }
  };
// --------------------------------------------------
// DOWNLOAD AI FLOOD RISK REPORT
// --------------------------------------------------
const downloadRiskReport = () => {
  if (!weatherData) {
    setError(
      "Please analyze a location before downloading the report."
    );
    return;
  }

  const prediction =
    testMode && testPrediction
      ? testPrediction
      : weatherData.prediction;

  const risk =
    prediction?.flood_risk || "UNKNOWN";

  const confidence =
    prediction?.confidence_percent ?? 0;

  const doc = new jsPDF();

  let y = 20;

  // --------------------------------------------------
  // HEADER
  // --------------------------------------------------

  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");

  doc.text(
    "AI Flood Risk Assessment Report",
    20,
    y
  );

  y += 12;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(
    `Generated: ${new Date().toLocaleString()}`,
    20,
    y
  );

  y += 14;

  // --------------------------------------------------
  // LOCATION
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "1. Location Information",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(
    `Location: ${
      selectedLocation || "Selected Location"
    }`,
    20,
    y
  );

  y += 6;

  doc.text(
    `Latitude: ${latitude}`,
    20,
    y
  );

  y += 6;

  doc.text(
    `Longitude: ${longitude}`,
    20,
    y
  );

  y += 12;

  // --------------------------------------------------
  // AI PREDICTION
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "2. AI Flood Risk Prediction",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(
    `Flood Risk Level: ${risk}`,
    20,
    y
  );

  y += 6;

  doc.text(
    `Model Confidence: ${confidence}%`,
    20,
    y
  );

  y += 6;

  doc.text(
    `AI Model: ${
      prediction?.model || "Random Forest"
    }`,
    20,
    y
  );

  y += 12;

  // --------------------------------------------------
  // WEATHER CONDITIONS
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "3. Weather Conditions",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

 const reportTemperature =
  testMode && testPrediction
    ? testPrediction.test_features?.temperature
    : weatherData.weather_conditions?.current_temperature_c;

const reportHumidity =
  testMode && testPrediction
    ? testPrediction.test_features?.humidity
    : weatherData.weather_conditions?.current_humidity_percent;

const reportCurrentRain =
  testMode && testPrediction
    ? testPrediction.test_features?.current_rain
    : weatherData.weather_conditions?.current_rain_mm;

doc.text(
  `Temperature: ${reportTemperature ?? "--"} °C`,
  20,
  y
);

y += 6;

doc.text(
  `Humidity: ${reportHumidity ?? "--"} %`,
  20,
  y
);

y += 6;

doc.text(
  `Current Rain: ${reportCurrentRain ?? "--"} mm`,
  20,
  y
);
  y += 12;
const reportRainfall24 =
  testMode && testPrediction
    ? testPrediction.test_features?.rainfall_24h
    : weatherData.rainfall_analysis?.next_24_hours_mm;

const reportRainfall72 =
  testMode && testPrediction
    ? testPrediction.test_features?.rainfall_72h
    : weatherData.rainfall_analysis?.next_72_hours_mm;

const reportPeakHourlyRain =
  testMode && testPrediction
    ? testPrediction.test_features?.max_hourly_rain
    : weatherData.rainfall_analysis?.maximum_hourly_rain_mm;
    // --------------------------------------------------
  // RAINFALL ANALYSIS
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "4. Rainfall Analysis",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(
  `Next 24 Hours: ${
  reportRainfall24 ?? "--"
 } mm`,  
    20,
    y
  );

  y += 6;

  doc.text(
    `Next 72 Hours: ${
  reportRainfall72 ?? "--"
    } mm`,
    20,
    y
  );

  y += 6;

  doc.text(
   `Peak Hourly Rainfall: ${
  reportPeakHourlyRain ?? "--" 
    } mm`,
    20,
    y
  );

  y += 12;

  // --------------------------------------------------
  // RISK FACTORS
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "5. Detected Risk Factors",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  const factors =
    testMode && testPrediction
      ? testPrediction.risk_factors
      : weatherData.risk_factors;

  if (factors?.length > 0) {
    factors.forEach((factor) => {

      const lines =
        doc.splitTextToSize(
          `• ${factor}`,
          170
        );

      doc.text(
        lines,
        20,
        y
      );

      y +=
        lines.length * 5 + 2;
    });
  } else {
    doc.text(
      "No major rainfall-related risk factors detected.",
      20,
      y
    );

    y += 6;
  }

  y += 6;

  // --------------------------------------------------
  // AI EXPLANATION
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "6. AI Risk Explanation",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  const explanation =
  testMode && testPrediction
    ? testPrediction.risk_explanation
    : weatherData.risk_explanation;

const finalExplanation =
  explanation ||
  "AI risk explanation unavailable.";
  const explanationLines =
  doc.splitTextToSize(
    finalExplanation,
    170
  );

  doc.text(
    explanationLines,
    20,
    y
  );

  y +=
    explanationLines.length * 5 + 10;

  // --------------------------------------------------
  // EARLY WARNING
  // --------------------------------------------------

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");

  doc.text(
    "7. Early Warning",
    20,
    y
  );

  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  doc.text(
    earlyWarning?.title ||
      "No early warning available.",
    20,
    y
  );

  y += 6;

  const warningLines =
    doc.splitTextToSize(
      earlyWarning?.message ||
        "No additional warning information available.",
      170
    );

  doc.text(
    warningLines,
    20,
    y
  );

  y +=
    warningLines.length * 5 + 12;

  // --------------------------------------------------
  // DISCLAIMER
  // --------------------------------------------------

  doc.setFontSize(9);
  doc.setFont("helvetica", "italic");

  const disclaimer =
    "Disclaimer: This report contains an AI-assisted rainfall-based flood risk estimate and is not an official flood warning.";

  const disclaimerLines =
    doc.splitTextToSize(
      disclaimer,
      170
    );

  doc.text(
    disclaimerLines,
    20,
    y
  );

  // --------------------------------------------------
  // SAVE PDF
  // --------------------------------------------------

  doc.save(
    "AI_Flood_Risk_Assessment_Report.pdf"
  );
};
 // --------------------------------------------------
  // CITY / LOCATION SEARCH
  // --------------------------------------------------
  const searchCity = async () => {
  if (!city.trim()) {
    setError("Please enter a city or location name.");
    return;
  }

  if (city.trim().length < 2) {
    setError(
      "Please enter at least 2 characters for location search."
    );
    return;
  }

  setSearchingLocation(true);
  setError("");
  setLocationResults([]);
  setTestPrediction(null);
  setTestMode(false);

  // Clear old location before a new search
  setSelectedLocation("");
  setLatitude("");
  setLongitude("");

  try {
    const response = await fetch(
      `https://local-weather-flood-risk.onrender.com/search-location?city=${encodeURIComponent(
        city.trim()
      )}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || "Location search failed."
      );
    }

    const results = data.results || [];

    setLocationResults(results);

    if (results.length === 0) {
      setError(
        `No matching location found for "${city.trim()}".`
      );
    }
  } catch (err) {
    console.error(err);

    setError(
      err.message ||
        "Location search failed. Make sure the Flask backend is running."
    );
  } finally {
    setSearchingLocation(false);
  }
};


  // --------------------------------------------------
  // CHOOSE LOCATION
  // --------------------------------------------------

  const chooseLocation = (place) => {
    setLatitude(String(place.latitude));
    setLongitude(String(place.longitude));

    const locationName = [
      place.name,
      place.district,
      place.state,
      place.country,
    ]
      .filter(Boolean)
      .join(", ");

    setSelectedLocation(locationName);
    setCity(place.name || "");

    setLocationResults([]);
    setWeatherData(null);
    setForecastData(null);
    setTestPrediction(null);
    setTestMode(false);
    setError("");
  };


  // --------------------------------------------------
  // PREDICTION HISTORY
  // --------------------------------------------------

  const getPredictionHistory = async () => {
    try {
      const response = await fetch(
        "https://local-weather-flood-risk.onrender.com/prediction-history"
      );

      if (!response.ok) {
        throw new Error(
          "Unable to fetch prediction history"
        );
      }

      const data = await response.json();

      setPredictionHistory(
        data.history || []
      );
    } catch (error) {
      console.error(
        "Prediction history error:",
        error
      );
    }
  };


  // --------------------------------------------------
  // FLOOD RISK ANALYSIS
  // --------------------------------------------------

  const getFloodRisk = async () => {
    setTestPrediction(null);
setTestMode(false);
    if (!latitude || !longitude) {
      setError(
        "Please enter latitude and longitude."
      );
      return;
    }

    const lat = Number(latitude);
    const lon = Number(longitude);

    if (
      Number.isNaN(lat) ||
      Number.isNaN(lon)
    ) {
      setError(
        "Latitude and longitude must be valid numbers."
      );
      return;
    }

    if (lat < -90 || lat > 90) {
      setError(
        "Latitude must be between -90 and 90."
      );
      return;
    }

    if (lon < -180 || lon > 180) {
      setError(
        "Longitude must be between -180 and 180."
      );
      return;
    }

    setLoading(true);
    setForecastData(null);
    setError("");
    setTestPrediction(null);
    setTestMode(false);

    try {
      const response = await fetch(
        "https://local-weather-flood-risk.onrender.com/flood-risk",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            latitude: lat,
            longitude: lon,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to fetch weather and flood-risk data."
        );
      }

      const data = await response.json();

      setWeatherData(data);
      generateEarlyWarning(data.prediction);
      setTestPrediction(null);
      setTestMode(false);

      await getPredictionHistory();


      // --------------------------------------------------
      // 3-DAY FORECAST
      // --------------------------------------------------

      const forecastResponse = await fetch(
        `https://local-weather-flood-risk.onrender.com/test-weather?lat=${lat}&lon=${lon}`
      );

      if (!forecastResponse.ok) {
        throw new Error(
          "Unable to fetch 3-day weather forecast."
        );
      }

      const forecast =
        await forecastResponse.json();

      setForecastData(forecast);

      // Always return to LIVE analysis after Analyze Risk.
      setTestPrediction(null);
      setTestMode(false);

      console.log(
        "3-Day Forecast Data:",
        forecast
      );
    } catch (err) {
      console.error(err);

      setError(
        "Backend connection failed. Make sure the Flask server is running."
      );

      setWeatherData(null);
    } finally {
      setLoading(false);
    }
  };


  // --------------------------------------------------
  // AI TEST PREDICTION
  // --------------------------------------------------

  const runTestPrediction = async (testCase) => {
  setTestMode(true);
  setTestPrediction(null);
  setError("");

  try {
    const response = await fetch(
      "https://local-weather-flood-risk.onrender.com/test-flood-risk",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          test_case: testCase,
        }),
      }
    );

const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error ||
          "AI test prediction failed."
      );
    }

    const testResult = {
  ...data.prediction,

  test_features:
    data.test_features || {},

  risk_factors:
    data.risk_factors || [],

  risk_explanation:
    data.risk_explanation || "",
};

setTestPrediction(testResult);

generateEarlyWarning(testResult);
  } catch (err) {
    console.error(err);

    setError(
      "AI test failed. Make sure the Flask backend is running."
    );
  }
};
  // --------------------------------------------------
  // DAILY FORECAST
  // --------------------------------------------------

  const getDailyForecast = () => {
    if (!forecastData?.forecast) {
      return [];
    }

    const {
      time,
      temperature,
      precipitation,
      humidity,
    } = forecastData.forecast;

    if (
      !time ||
      !temperature ||
      !precipitation ||
      !humidity
    ) {
      return [];
    }

    const dailyData = {};

    time.forEach((dateTime, index) => {
      const date =
        dateTime.split("T")[0];

      if (!dailyData[date]) {
        dailyData[date] = {
          date,
          temperatures: [],
          precipitation: [],
          humidity: [],
        };
      }

      dailyData[date].temperatures.push(
        temperature[index]
      );

      dailyData[date].precipitation.push(
        precipitation[index]
      );

      dailyData[date].humidity.push(
        humidity[index]
      );
    });

    return Object.values(dailyData)
      .slice(0, 3)
      .map((day) => ({
        date: day.date,

        maxTemp: Math.max(
          ...day.temperatures
        ).toFixed(1),

        minTemp: Math.min(
          ...day.temperatures
        ).toFixed(1),

        rainfall: day.precipitation
          .reduce(
            (sum, value) =>
              sum + (value || 0),
            0
          )
          .toFixed(1),

        humidity: Math.round(
          day.humidity.reduce(
            (sum, value) =>
              sum + (value || 0),
            0
          ) / day.humidity.length
        ),
      }));
  };


  const dailyForecast =
    getDailyForecast();


  // --------------------------------------------------
  // DISPLAY PREDICTION
  // --------------------------------------------------

  const displayPrediction =
    testMode && testPrediction
      ? testPrediction
      : weatherData?.prediction || null;

  const risk =
    displayPrediction?.flood_risk ||
    "UNKNOWN";

  const probabilities =
    displayPrediction?.class_probabilities ||
    {};

  const displayConfidence =
    Number(
      displayPrediction?.confidence_percent ?? 0
    );


  // --------------------------------------------------
  // RISK PROBABILITIES
  // --------------------------------------------------

  const highProbability =
    Number(probabilities.HIGH || 0);

  const mediumProbability =
    Number(probabilities.MEDIUM || 0);

  const lowProbability =
    Number(probabilities.LOW || 0);


  // --------------------------------------------------
  // AI RISK SCORE
  // --------------------------------------------------

  const aiRiskScore = Math.max(
    1,
    Math.min(
      100,
      Math.round(
        highProbability +
          mediumProbability * 0.5
      )
    )
  );


  // --------------------------------------------------
  // RISK CLASS
  // --------------------------------------------------

  const riskClass =
    risk === "HIGH"
      ? "risk-high"
      : risk === "MEDIUM"
      ? "risk-medium"
      : risk === "LOW"
      ? "risk-low"
      : "risk-unknown";


  // --------------------------------------------------
  // JSX
  // --------------------------------------------------

  return (
    <div className="app">

      {/* --------------------------------------------------
          HEADER
      -------------------------------------------------- */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            <CloudRain size={30} />
          </div>

          <div>
            <h1>
              Local Weather & Flood Risk
            </h1>

            <p>
              AI-Powered Weather Monitoring &
              Flood Risk Prediction
            </p>
          </div>

        </div>


        <div className="system-status">
          <span className="status-dot"></span>
          AI System Active
        </div>

      </header>


      <main className="dashboard">

        {/* --------------------------------------------------
            HERO
        -------------------------------------------------- */}

        <section className="hero-section">

          <div className="hero-content">

            <span className="hero-badge">
              <ShieldAlert size={16} />
              AI Flood Risk Intelligence
            </span>

            <h2>
              Know the weather.
              <br />
              <span>
                Understand the risk.
              </span>
            </h2>

            <p>
              Real-time weather monitoring
              combined with machine learning
              to estimate rainfall-based flood
              risk for your selected location.
            </p>

          </div>


          <div className="hero-visual">
            <Waves size={110} />
          </div>

        </section>


        {/* --------------------------------------------------
            TEST MODE BANNER
        -------------------------------------------------- */}

        {testMode && testPrediction && (
          <div className="test-mode-banner">
            🧪 AI Test Mode Active
            {testPrediction
              ? ` — Simulated ${testPrediction.flood_risk} Risk Scenario`
              : " — Select LOW, MEDIUM or HIGH"}
          </div>
        )}


        {/* --------------------------------------------------
            SEARCH CARD
        -------------------------------------------------- */}

        <section className="search-card">

          <div className="section-title">

            <MapPin size={21} />

            <div>

              <h3>
                Check Flood Risk
              </h3>

              <p>
                Search for a city or use
                coordinates to analyze
                current conditions.
              </p>

            </div>

          </div>


          {/* CITY SEARCH */}

          <div className="city-search-section">

            <label>
              City / Location
            </label>


            <div className="city-search-row">

              <div className="input-box city-input">

                <MapPin size={18} />

                <input
                  type="text"
                  value={city}
                  onChange={(e) => {
                    setCity(
                      e.target.value
                    );
                    setSelectedLocation("");
                  }}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter"
                    ) {
                      searchCity();
                    }
                  }}
                  placeholder="Search city e.g. Lucknow"
                />

              </div>


              <button
                type="button"
                className="location-search-button"
                onClick={searchCity}
                disabled={searchingLocation}
              >

                {searchingLocation ? (
                  <>
                    <LoaderCircle
                      className="spinner"
                      size={18}
                    />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search size={18} />
                    Search Location
                  </>
                )}

              </button>

            </div>


            {/* SELECTED LOCATION */}

            {selectedLocation && (
              <div className="selected-location-message">

                <MapPin size={16} />

                Selected:
                <strong>
                  {selectedLocation}
                </strong>

              </div>
            )}


            {/* SEARCH RESULTS */}

            {locationResults.length > 0 && (
              <div className="location-results">

                {locationResults.map(
                  (place, index) => (

                    <button
                      type="button"
                      className="location-result-item"
                      key={`${place.latitude}-${place.longitude}-${index}`}
                      onClick={() =>
                        chooseLocation(place)
                      }
                    >

                      <MapPin size={18} />

                      <div>

                        <strong>
                          {place.name}
                        </strong>

                        <span>
                          {[
                            place.district,
                            place.state,
                            place.country,
                          ]
                            .filter(Boolean)
                            .join(", ")}
                        </span>

                        <small>
                          {place.latitude},{" "}
                          {place.longitude}
                        </small>

                      </div>

                    </button>

                  )
                )}

              </div>
            )}

          </div>


          {/* --------------------------------------------------
              COORDINATES + BUTTONS
          -------------------------------------------------- */}

          <div className="search-controls">

            {/* LATITUDE */}

            <div className="input-group">

              <label>
                Latitude
              </label>

              <div className="input-box">

                <Navigation size={18} />

                <input
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={(e) => {
                    setLatitude(
                      e.target.value
                    );
                    setSelectedLocation("");
                  }}
                  placeholder="Enter latitude"
                />

              </div>

            </div>


            {/* LONGITUDE */}

            <div className="input-group">

              <label>
                Longitude
              </label>

              <div className="input-box">

                <Navigation size={18} />

                <input
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={(e) => {
                    setLongitude(
                      e.target.value
                    );
                    setSelectedLocation("");
                  }}
                  placeholder="Enter longitude"
                />

              </div>

            </div>


            {/* ANALYZE BUTTON */}

            <button
              type="button"
              className="analyze-button"
              onClick={getFloodRisk}
              disabled={loading}
            >

              {loading ? (
                <>
                  <LoaderCircle
                    className="spinner"
                    size={19}
                  />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search size={19} />
                  Analyze Risk
                </>
              )}

            </button>


            {/* AI TEST MODE BUTTON */}

            <button
              type="button"
              className="test-mode-button"
              onClick={() => {
                const newMode =
                  !testMode;

                setTestMode(newMode);

                if (!newMode) {
  setTestPrediction(null);
  generateEarlyWarning(weatherData?.prediction);
}
              }}
            >
              🧪{" "}
              {testMode
                ? "Exit AI Test Mode"
                : "AI Test Mode"}
            </button>
<button
  type="button"
  className="download-report-button"
  onClick={downloadRiskReport}
  disabled={!weatherData}
>
  📥 Download AI Report
</button>

            {/* --------------------------------------------------
                TEST SCENARIOS
            -------------------------------------------------- */}

            {testMode && (
              <div className="test-scenarios">

                <span>
                  Test Scenario:
                </span>


                <button
                  type="button"
                  className={
                    testPrediction?.flood_risk ===
                    "LOW"
                      ? "active-test"
                      : ""
                  }
                  onClick={() =>
                    runTestPrediction("LOW")
                  }
                >
                  LOW
                </button>


                <button
                  type="button"
                  className={
                    testPrediction?.flood_risk ===
                    "MEDIUM"
                      ? "active-test"
                      : ""
                  }
                  onClick={() =>
                    runTestPrediction("MEDIUM")
                  }
                >
                  MEDIUM
                </button>


                <button
                  type="button"
                  className={
                    testPrediction?.flood_risk ===
                    "HIGH"
                      ? "active-test"
                      : ""
                  }
                  onClick={() =>
                    runTestPrediction("HIGH")
                  }
                >
                  HIGH
                </button>


                {testPrediction && (
                  <strong className="active-test-label">
                    Active:{" "}
                    {testPrediction.flood_risk}
                  </strong>
                )}

              </div>
            )}


            {/* ERROR */}

            {error && (
              <div className="error-message">

                <AlertTriangle size={18} />

                {error}

              </div>
            )}

          </div>

        </section>


        {/* --------------------------------------------------
            INITIAL STATE
        -------------------------------------------------- */}

        {!weatherData ? (

          <section className="welcome-card">

            <div className="welcome-icon">
              <CloudRain size={48} />
            </div>

            <h3>
              Weather Intelligence Ready
            </h3>

            <p>
              Search for a city above or enter
              coordinates, then click
              <strong>
                {" "}Analyze Risk
              </strong>{" "}
              to view live weather conditions
              and AI-assisted flood-risk analysis.
            </p>

          </section>

        ) : (

          <>
            {/* --------------------------------------------------
                CURRENT LOCATION
            -------------------------------------------------- */}

            <section className="location-row">

              <div>

                <p className="eyebrow">
                  CURRENT ANALYSIS
                </p>

                <h2>
                  <MapPin size={24} />

                  {selectedLocation ||
                    "Selected Location"}
                </h2>

              </div>


              <div className="coordinates">

                {weatherData.location
                  ?.latitude
                  ?.toFixed?.(4) ??
                  weatherData.location
                    ?.latitude}

                ,{" "}

                {weatherData.location
                  ?.longitude
                  ?.toFixed?.(4) ??
                  weatherData.location
                    ?.longitude}

              </div>

            </section>


            {/* --------------------------------------------------
                MAIN METRICS
            -------------------------------------------------- */}

            <section className="metrics-grid">

              {/* TEMPERATURE */}

              <article className="metric-card">

                <div className="metric-icon temperature">
                  <Thermometer size={25} />
                </div>

                <div>

                  <p>
                    Temperature
                  </p>

                  <h3>
                    {weatherData
                      .weather_conditions
                      ?.current_temperature_c ??
                      "--"}
                    °C
                  </h3>

                  <span>
                    Current temperature
                  </span>

                </div>

              </article>


              {/* HUMIDITY */}

              <article className="metric-card">

                <div className="metric-icon humidity">
                  <Droplets size={25} />
                </div>

                <div>

                  <p>
                    Humidity
                  </p>

                  <h3>
                    {weatherData
                      .weather_conditions
                      ?.current_humidity_percent ??
                      "--"}
                    %
                  </h3>

                  <span>
                    Relative humidity
                  </span>

                </div>

              </article>


              {/* CURRENT RAIN */}

              <article className="metric-card">

                <div className="metric-icon rainfall">
                  <CloudRain size={25} />
                </div>

                <div>

                  <p>
                    Current Rain
                  </p>

                  <h3>
                    {weatherData
                      .weather_conditions
                      ?.current_rain_mm ??
                      "--"}{" "}
                    mm
                  </h3>

                  <span>
                    Live rainfall
                  </span>

                </div>

              </article>


              {/* WATER FEATURE */}

              <article className="metric-card">

                <div className="metric-icon water">
                  <Waves size={25} />
                </div>

                <div>

                  <p>

                    {weatherData
                      .weather_conditions
                      ?.nearby_water_feature

                      ? Number(
                          weatherData
                            .weather_conditions
                            .nearby_water_feature
                            .distance_km
                        ) <= 5
                        ? "Nearby Water Feature"
                        : "Nearest Water Feature"

                      : "Water Feature"}

                  </p>


                  <h3>

                    {weatherData
                      .weather_conditions
                      ?.nearby_water_feature
                      ?.name ??
                      "--"}

                  </h3>


                  <span>

                    {weatherData
                      .weather_conditions
                      ?.nearby_water_feature
                      ?.distance_km !=
                    null
                      ? `${weatherData.weather_conditions.nearby_water_feature.distance_km} km away`
                      : "No water feature detected"}

                  </span>

                </div>

              </article>


              {/* MAX HOURLY RAIN */}

              <article className="metric-card">

                <div className="metric-icon intensity">
                  <Wind size={25} />
                </div>

                <div>

                  <p>
                    Max Hourly Rain
                  </p>

                  <h3>

                    {weatherData
                      .rainfall_analysis
                      ?.maximum_hourly_rain_mm ??
                      "--"}{" "}
                    mm

                  </h3>

                  <span>
                    Rainfall intensity
                  </span>

                </div>

              </article>


              {/* ELEVATION */}

              <article className="metric-card">

                <div className="metric-icon elevation">
                  <Navigation size={25} />
                </div>

                <div>

                  <p>
                    Elevation
                  </p>

                  <h3>

                    {weatherData
                      .weather_conditions
                      ?.elevation_m ??
                      "--"}{" "}
                    m

                  </h3>

                  <span>
                    Terrain elevation
                  </span>

                </div>

              </article>

            </section>


            {/* --------------------------------------------------
                RISK + RAINFALL
            -------------------------------------------------- */}

            <section className="analysis-grid">

              {/* AI RISK CARD */}

              <article
                className={`risk-card ${riskClass}`}
              >

                <div className="risk-header">

                  <div>

                    <p className="eyebrow">
                      AI PREDICTION
                    </p>

                    <h3>
                      Flood Risk Level
                    </h3>

                  </div>

                  <ShieldAlert size={34} />

                </div>


                {/* RISK BADGE */}

                <div
                  className={`risk-level risk-badge ${riskClass}`}
                >
                  {risk}
                </div>


                {/* MODEL CONFIDENCE */}

                <div className="confidence-section">

                  <div className="confidence-row">

                    <span>
                      Model confidence
                    </span>

                    <strong>
                      {displayConfidence.toFixed(
                        2
                      )}
                      %
                    </strong>

                  </div>


                  <div className="confidence-track">

                    <div
                      className="confidence-fill"
                      style={{
                        width: `${Math.min(
                          displayConfidence,
                          100
                        )}%`,
                      }}
                    ></div>

                  </div>

                </div>


                {/* AI RISK SCORE */}

                <div className="risk-score-section">

                  <div className="risk-score-header">

                    <span>
                      AI Risk Score
                    </span>

                    <strong>
                      {aiRiskScore} /100
                    </strong>

                  </div>


                  <div className="risk-score-track">

                    <div
                      className={`risk-score-fill ${riskClass}`}
                      style={{
                        width: `${aiRiskScore}%`,
                      }}
                    ></div>

                  </div>


                  <p className="risk-score-note">
                    Score is calculated from
                    the AI model's predicted
                    risk probabilities.
                  </p>


                  <p
                    className={`risk-score-status ${riskClass}`}
                  >

                    {aiRiskScore <= 30
                      ? "Low Risk — Current conditions indicate relatively low rainfall-based flood risk."

                      : aiRiskScore <= 60
                      ? "Moderate Risk — Weather conditions require continued monitoring."

                      : "High Risk — Current weather conditions indicate elevated rainfall-based flood risk."}

                  </p>

                </div>


                {/* MODEL NAME */}

                <p className="model-name">

                  Model:{" "}
                  {displayPrediction?.model ||
                    "Random Forest"}

                </p>


                {/* RISK PROBABILITY */}

                <div className="probability-breakdown">

                  <p className="probability-title">
                    Risk Probability
                  </p>


                  {/* HIGH */}

                  <div className="probability-item">

                    <div className="probability-label">

                      <span>
                        HIGH
                      </span>

                      <strong>
                        {highProbability.toFixed(
                          2
                        )}
                        %
                      </strong>

                    </div>


                    <div className="probability-track high-track">

                      <div
                        className="probability-fill high-fill"
                        style={{
                          width: `${Math.min(
                            highProbability,
                            100
                          )}%`,
                        }}
                      ></div>

                    </div>

                  </div>


                  {/* MEDIUM */}

                  <div className="probability-item">

                    <div className="probability-label">

                      <span>
                        MEDIUM
                      </span>

                      <strong>
                        {mediumProbability.toFixed(
                          2
                        )}
                        %
                      </strong>

                    </div>


                    <div className="probability-track medium-track">

                      <div
                        className="probability-fill medium-fill"
                        style={{
                          width: `${Math.min(
                            mediumProbability,
                            100
                          )}%`,
                        }}
                      ></div>

                    </div>

                  </div>


                  {/* LOW */}

                  <div className="probability-item">

                    <div className="probability-label">

                      <span>
                        LOW
                      </span>

                      <strong>
                        {lowProbability.toFixed(
                          2
                        )}
                        %
                      </strong>

                    </div>


                    <div className="probability-track low-track">

                      <div
                        className="probability-fill low-fill"
                        style={{
                          width: `${Math.min(
                            lowProbability,
                            100
                          )}%`,
                        }}
                      ></div>

                    </div>

                  </div>

                </div>

              </article>


              {/* RAINFALL ANALYSIS */}

              <article className="rainfall-card">

                <div className="section-title">

                  <CloudRain size={22} />

                  <div>

                    <h3>
                      Rainfall Analysis
                    </h3>

                    <p>
                      Forecast rainfall accumulation
                    </p>

                  </div>

                </div>


                <div className="rainfall-stats">

                  <div>

                    <span>
                      Next 24 Hours
                    </span>

                    <strong>
                      {weatherData
                        .rainfall_analysis
                        ?.next_24_hours_mm ??
                        "--"}{" "}
                      mm
                    </strong>

                  </div>


                  <div>

                    <span>
                      Next 72 Hours
                    </span>

                    <strong>
                      {weatherData
                        .rainfall_analysis
                        ?.next_72_hours_mm ??
                        "--"}{" "}
                      mm
                    </strong>

                  </div>


                  <div>

                    <span>
                      Peak Hourly
                    </span>

                    <strong>
                      {weatherData
                        .rainfall_analysis
                        ?.maximum_hourly_rain_mm ??
                        "--"}{" "}
                      mm
                    </strong>

                  </div>

                </div>

              </article>

            </section>


            {/* --------------------------------------------------
                3 DAY FORECAST
            -------------------------------------------------- */}

            {dailyForecast.length > 0 && (
              <section className="forecast-section">

                <h3>
                  3-Day Weather Forecast
                </h3>


                <div className="forecast-grid">

                  {dailyForecast.map(
                    (day) => (

                      <article
                        className="forecast-card"
                        key={day.date}
                      >

                        <strong>

                          {new Date(
                            `${day.date}T00:00:00`
                          ).toLocaleDateString(
                            "en-US",
                            {
                              weekday:
                                "long",
                            }
                          )}

                        </strong>


                        <span className="forecast-date">

                          {new Date(
                            `${day.date}T00:00:00`
                          ).toLocaleDateString(
                            "en-US",
                            {
                              day: "numeric",
                              month: "short",
                            }
                          )}

                        </span>


                        <p>
                          {day.maxTemp}°C /{" "}
                          {day.minTemp}°C
                        </p>

                        <p>
                          Rainfall:{" "}
                          {day.rainfall} mm
                        </p>

                        <p>
                          Humidity:{" "}
                          {day.humidity}%
                        </p>

                      </article>

                    )
                  )}

                </div>

              </section>
            )}


            {/* --------------------------------------------------
                RAINFALL CHART
            -------------------------------------------------- */}

            {dailyForecast.length > 0 && (
              <section className="rainfall-chart-section">

                <h3>
                  3-Day Rainfall Forecast
                </h3>


                <div
                  style={{
                    width: "100%",
                    height: 300,
                  }}
                >

                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >

                    <BarChart
                      data={dailyForecast}
                      margin={{
                        top: 10,
                        right: 10,
                        left: 5,
                        bottom: 5,
                      }}
                    >

                      <CartesianGrid
                        strokeDasharray="3 3"
                      />


                      <XAxis
                        dataKey="date"
                        tickFormatter={(date) =>
                          new Date(
                            `${date}T00:00:00`
                          ).toLocaleDateString(
                            "en-US",
                            {
                              weekday: "short",
                            }
                          )
                        }
                      />


                      <YAxis
                        tickFormatter={(value) =>
                          `${value} mm`
                        }
                      />


                      <Tooltip
                        formatter={(value) => [
                          `${value} mm`,
                          "Rainfall",
                        ]}
                        labelFormatter={(date) =>
                          new Date(
                            `${date}T00:00:00`
                          ).toLocaleDateString(
                            "en-US",
                            {
                              weekday:
                                "long",
                              month: "short",
                              day: "numeric",
                            }
                          )
                        }
                      />


                      <Bar
                        dataKey="rainfall"
                        fill="#0f6fff"
                        radius={[
                          8,
                          8,
                          0,
                          0,
                        ]}
                      />

                    </BarChart>

                  </ResponsiveContainer>

                </div>

              </section>
            )}


            {/* --------------------------------------------------
                MAP
            -------------------------------------------------- */}

            <section className="risk-map-section">

              <div className="section-title">

                <MapPin size={22} />

                <div>

                  <h3>
                    Location & Flood Risk Map
                  </h3>

                  <p>
                    Selected location with
                    the current AI flood-risk
                    estimate.
                  </p>

                </div>

              </div>


              <div className="map-container">

                <MapContainer
                  center={[
                    Number(latitude),
                    Number(longitude),
                  ]}
                  zoom={11}
                  style={{
                    height: "350px",
                    width: "100%",
                  }}
                >

                  <MapUpdater
                    latitude={latitude}
                    longitude={longitude}
                  />


                  <TileLayer
                    attribution="&copy; OpenStreetMap contributors"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />


                  <Marker
                    position={[
                      Number(latitude),
                      Number(longitude),
                    ]}
                  >

                    <Popup>

                      <div className="map-popup">

                        <strong className="map-popup-title">

                          {selectedLocation ||
                            "Selected Location"}

                        </strong>


                        <div className="map-popup-row">

                          <span>
                            Flood Risk
                          </span>

                          <strong>
                            {displayPrediction
                              ?.flood_risk ||
                              "N/A"}
                          </strong>

                        </div>


                        <div className="map-popup-row">

                          <span>
                            AI Confidence
                          </span>

                          <strong>
                            {displayConfidence
                              ? `${displayConfidence.toFixed(
                                  2
                                )}%`
                              : "--"}
                          </strong>

                        </div>


                        <div className="map-popup-row">

                          <span>
                            24h Rainfall
                          </span>

                          <strong>
                            {weatherData
                              .rainfall_analysis
                              ?.next_24_hours_mm ??
                              "--"}{" "}
                            mm
                          </strong>

                        </div>

                      </div>

                    </Popup>

                  </Marker>

                </MapContainer>

              </div>

            </section>

{/* --------------------------------------------------
    ADVANCED EARLY WARNING ALERT
-------------------------------------------------- */}

{earlyWarning && (
  <section
    className={`early-warning-alert ${earlyWarning.level.toLowerCase()}`}
  >

    <div className="early-warning-icon">

      {earlyWarning.level === "HIGH"
        ? "🚨"
        : earlyWarning.level === "MEDIUM"
        ? "⚠️"
        : "🟢"}

    </div>

    <div className="early-warning-content">

      <h3>
        {earlyWarning.title}
      </h3>

      <p>
        {earlyWarning.message}
      </p>

      {/* ACTIONABLE RECOMMENDATIONS */}

      <div className="early-warning-actions">

        <strong>
          Recommended Actions
        </strong>

        {earlyWarning.level === "HIGH" ? (

          <ul>
            <li>
              🚨 Avoid unnecessary travel through
              low-lying or waterlogged areas.
            </li>

            <li>
              📢 Closely monitor official weather
              and local emergency updates.
            </li>

            <li>
              🏠 Keep essential documents,
              medicines and emergency supplies ready.
            </li>

            <li>
              ⚡ Be prepared for rapid changes
              in rainfall conditions.
            </li>
          </ul>

        ) : earlyWarning.level === "MEDIUM" ? (

          <ul>
            <li>
              ⚠️ Monitor rainfall and weather
              conditions regularly.
            </li>

            <li>
              🌧️ Pay attention to low-lying areas
              and local drainage conditions.
            </li>

            <li>
              📱 Keep weather and emergency
              notifications enabled.
            </li>
          </ul>

        ) : (

          <ul>
            <li>
              🟢 Continue normal activities
              while monitoring weather updates.
            </li>

            <li>
              🌦️ Check future rainfall forecasts
              for changing conditions.
            </li>
          </ul>

        )}

      </div>

    </div>

  </section>
)}
            {/* --------------------------------------------------
                AI RISK EXPLANATION
            -------------------------------------------------- */}

            {weatherData?.risk_explanation && (
              <section className="risk-explanation">

                <h3>
                  🤖 AI Risk Explanation
                </h3>

                <p>

                  {testMode &&
                  testPrediction

                    ? testPrediction.flood_risk ===
                      "HIGH"

                      ? `AI test scenario predicts HIGH flood risk with ${testPrediction.confidence_percent}% confidence based on simulated heavy-rainfall conditions.`

                      : testPrediction.flood_risk ===
                        "MEDIUM"

                      ? `AI test scenario predicts MEDIUM flood risk with ${testPrediction.confidence_percent}% confidence based on simulated moderate-rainfall conditions.`

                      : `AI test scenario predicts LOW flood risk with ${testPrediction.confidence_percent}% confidence based on simulated low-rainfall conditions.`

                    : weatherData.risk_explanation}

                </p>

              </section>
            )}


            {/* --------------------------------------------------
                RISK FACTORS
            -------------------------------------------------- */}

            <section className="risk-factors-card">

              <div className="section-title">

                <AlertTriangle size={22} />

                <div>

                  <h3>
                    Detected Risk Factors
                  </h3>

                  <p>
                    Conditions influencing
                    the current AI risk estimate.
                  </p>

                </div>

              </div>


              <div className="risk-factor-list">

                {(testMode
  ? testPrediction?.risk_factors
  : weatherData?.risk_factors
)?.length > 0 ? (

  (testMode
    ? testPrediction.risk_factors
    : weatherData.risk_factors
  ).map(
    (factor, index) => (

                      <div
                        className="risk-factor"
                        key={index}
                      >

                        <span>
                          {index + 1}
                        </span>

                        <p>
                          {factor}
                        </p>

                      </div>

                    )
                  )

                ) : (

                  <div className="safe-message">

                    No major rainfall-related
                    risk factors detected.

                  </div>

                )}

              </div>

            </section>


            {/* --------------------------------------------------
                FLOOD RISK ALERT
            -------------------------------------------------- */}

            <section
              className={`flood-alert flood-alert-${risk.toLowerCase()}`}
            >

              <AlertTriangle size={24} />

              <div>

                <h3>
                  Flood Risk Alert
                </h3>

                <p>

                  {risk === "HIGH"

                    ? "High flood risk detected. Avoid flood-prone areas and closely monitor official local warnings."

                    : risk === "MEDIUM"

                    ? "Moderate flood risk detected. Stay alert and continue monitoring rainfall and local conditions."

                    : risk === "LOW"

                    ? "Low flood risk detected for the selected location. Continue monitoring weather updates."

                    : "Flood risk information is currently unavailable."}

                </p>

              </div>

            </section>

{/* --------------------------------------------------
    PREDICTION HISTORY ANALYTICS
-------------------------------------------------- */}

{predictionHistory.length > 0 && (
  <section className="prediction-analytics">

    <div className="section-title">
      <ShieldAlert size={22} />

      <div>
        <h3>Prediction Analytics</h3>

        <p>
          Historical AI flood-risk prediction distribution.
        </p>
      </div>
    </div>

    <div className="analytics-chart-card">

      <ResponsiveContainer
        width="100%"
        height={300}
      >
        <BarChart
          data={[
            {
              risk: "LOW",
              count: predictionHistory.filter(
                (item) =>
                  String(item.flood_risk).toUpperCase() ===
                  "LOW"
              ).length,
            },
            {
              risk: "MEDIUM",
              count: predictionHistory.filter(
                (item) =>
                  String(item.flood_risk).toUpperCase() ===
                  "MEDIUM"
              ).length,
            },
            {
              risk: "HIGH",
              count: predictionHistory.filter(
                (item) =>
                  String(item.flood_risk).toUpperCase() ===
                  "HIGH"
              ).length,
            },
          ]}
        >

          <CartesianGrid
            strokeDasharray="3 3"
          />

          <XAxis
            dataKey="risk"
          />

          <YAxis
            allowDecimals={false}
          />

          <Tooltip />

          <Bar
            dataKey="count"
            name="Predictions"
            radius={[8, 8, 0, 0]}
          />

        </BarChart>
      </ResponsiveContainer>

    </div>

  </section>
)}
{/* --------------------------------------------------
    AI CONFIDENCE TREND
-------------------------------------------------- */}

{predictionHistory.length > 1 && (
  <section className="confidence-trend">

    <div className="section-title">

      <ShieldAlert size={22} />

      <div>
        <h3>AI Confidence Trend</h3>

        <p>
          Confidence variation across recent AI predictions.
        </p>
      </div>

    </div>

    <div className="confidence-chart-card">

      <ResponsiveContainer
        width="100%"
        height={300}
      >

        <LineChart
          data={predictionHistory
            .slice()
            .reverse()
            .map((item, index) => ({
              prediction: `#${index + 1}`,
              confidence:
                Number(item.confidence) || 0,
            }))
          }
        >

          <CartesianGrid
            strokeDasharray="3 3"
          />

          <XAxis
            dataKey="prediction"
          />

          <YAxis
            domain={[0, 100]}
            unit="%"
          />

          <Tooltip
            formatter={(value) => [
              `${value}%`,
              "Confidence",
            ]}
          />

          <Line
            type="monotone"
            dataKey="confidence"
            name="AI Confidence"
            stroke="#2563eb"
            strokeWidth={3}
            dot={{
              r: 4,
            }}
            activeDot={{
              r: 6,
            }}
          />

        </LineChart>

      </ResponsiveContainer>

    </div>

  </section>
)}
{/* --------------------------------------------------
    RAINFALL VS AI RISK ANALYTICS
-------------------------------------------------- */}

{predictionHistory.length > 1 && (
  <section className="rainfall-risk-analytics">

    <div className="section-title">

      <ShieldAlert size={22} />

      <div>
        <h3>Rainfall vs AI Risk</h3>

        <p>
          Relationship between recent rainfall and AI risk level.
        </p>
      </div>

    </div>

    <div className="rainfall-risk-chart-card">

      <ResponsiveContainer
        width="100%"
        height={320}
      >

        <ScatterChart>

          <CartesianGrid
            strokeDasharray="3 3"
          />

          <XAxis
            type="number"
            dataKey="rainfall"
            name="24h Rainfall"
            unit=" mm"
          />

          <YAxis
            type="number"
            dataKey="riskScore"
            name="AI Risk"
            domain={[0, 100]}
            unit=""
          />

          <Tooltip
            cursor={{
              strokeDasharray: "3 3",
            }}
          />

          <Scatter
            name="AI Risk Predictions"
            data={predictionHistory.map(
              (item) => {

                const risk =
                  String(
                    item.flood_risk || ""
                  ).toUpperCase();

                return {
                  rainfall:
                    Number(
                      item.rainfall_24h
                    ) || 0,

                  riskScore:
                    risk === "HIGH"
                      ? 100
                      : risk === "MEDIUM"
                      ? 50
                      : 0,
                };
              }
            )}
            fill="#2563eb"
          />

        </ScatterChart>

      </ResponsiveContainer>

    </div>

  </section>
)}
            {/* --------------------------------------------------
                PREDICTION HISTORY
            -------------------------------------------------- */}

            <section className="prediction-history">

              <div className="section-title">

                <ShieldAlert size={22} />

                <div>

                  <h3>
                    Prediction History
                  </h3>

                  <p>
                    Recent flood-risk
                    predictions saved by
                    the system.
                  </p>

                </div>

              </div>


              {predictionHistory.length ===
              0 ? (

                <p className="history-empty">
                  No prediction history
                  available yet.
                </p>

              ) : (

                <div className="history-table-wrapper">

                  <table className="history-table">

                    <thead>

                      <tr>

                        <th>
                          Risk
                        </th>

                        <th>
                          Confidence
                        </th>

                        <th>
                          24h Rain
                        </th>

                        <th>
                          72h Rain
                        </th>

                        <th>
                          Temp.
                        </th>

                        <th>
                          Humidity
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {predictionHistory.map(
                        (item) => (

                          <tr
                            key={item.id}
                          >

                            <td>

                              <span
                                className={`history-risk history-risk-${String(
                                  item.flood_risk
                                ).toLowerCase()}`}
                              >
                                {item.flood_risk}
                              </span>

                            </td>


                            <td>
                              {item.confidence}%
                            </td>


                            <td>
                              {item.rainfall_24h} mm
                            </td>


                            <td>
                              {item.rainfall_72h} mm
                            </td>


                            <td>
                              {item.temperature}°C
                            </td>


                            <td>
                              {item.humidity}%
                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>


            {/* --------------------------------------------------
                DISCLAIMER
            -------------------------------------------------- */}

            <section className="disclaimer">

              <AlertTriangle size={20} />

              <p>

                {weatherData.disclaimer ||
                  "Flood risk is an AI-assisted rainfall-based estimate and is not an official flood warning."}

              </p>

            </section>

          </>

        )}

      </main>


      {/* --------------------------------------------------
          FOOTER
      -------------------------------------------------- */}

      <footer>

        <p>
          Local Weather & Flood Risk Prediction
          System • AI-Assisted Weather Intelligence
        </p>

      </footer>

    </div>
  );
}


export default App;