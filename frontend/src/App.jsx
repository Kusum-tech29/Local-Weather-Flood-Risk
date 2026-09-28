import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  CloudRain,
  Droplets,
  MapPin,
  Search,
  ShieldAlert,
  Thermometer,
  Waves,
  Wind,
  AlertTriangle,
  Navigation,
  LoaderCircle,
} from "lucide-react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

import "./App.css";
function MapUpdater({ latitude, longitude }) {
  const map = useMap();

  map.setView([Number(latitude), Number(longitude)], 11);

  return null;
}
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
  const [error, setError] = useState("");

  // --------------------------------------------------
  // CITY / LOCATION SEARCH
  // --------------------------------------------------

  const searchCity = async () => {
    if (!city.trim()) {
      setError("Please enter a city or location name.");
      return;
    }
    if (city.trim().length < 2) {
  setError("Please enter at least 2 characters for location search.");
  return;
}

    setSearchingLocation(true);
    setError("");
    setLocationResults([]);

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/search-location?city=${encodeURIComponent(
          city.trim()
        )}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Location search failed.");
      }

      setLocationResults(data.results || []);

      if (!data.results || data.results.length === 0) {
        setError("No matching location found.");
      }
    } catch (err) {
      setError(
        "Location search failed. Make sure the Flask backend is running."
      );
    } finally {
      setSearchingLocation(false);
    }
  };

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
    setError("");
  };

  // --------------------------------------------------
  // FLOOD RISK ANALYSIS
  // --------------------------------------------------
const getPredictionHistory = async () => {
  try {
    const response = await fetch(
      "http://127.0.0.1:5000/prediction-history"
    );

    if (!response.ok) {
      throw new Error("Unable to fetch prediction history");
    }

    const data = await response.json();

    setPredictionHistory(data.history || []);
  } catch (error) {
    console.error("Prediction history error:", error);
  }
};
  const getFloodRisk = async () => {
   if (!latitude || !longitude) {
  setError("Please enter latitude and longitude.");
  return;
}

const lat = Number(latitude);
const lon = Number(longitude);

if (
  Number.isNaN(lat) ||
  Number.isNaN(lon)
) {
  setError("Latitude and longitude must be valid numbers.");
  return;
}

if (lat < -90 || lat > 90) {
  setError("Latitude must be between -90 and 90.");
  return;
}

if (lon < -180 || lon > 180) {
  setError("Longitude must be between -180 and 180.");
  return;
}  
    setLoading(true);
    setForecastData(null);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/flood-risk?lat=${latitude}&lon=${longitude}`
      );

      if (!response.ok) {
        throw new Error("Unable to fetch weather and flood-risk data.");
      }

      const data = await response.json();
      setWeatherData(data);
      await getPredictionHistory();
     const forecastResponse = await fetch(
  `http://127.0.0.1:5000/test-weather?lat=${latitude}&lon=${longitude}`
);

if (!forecastResponse.ok) {
  throw new Error("Unable to fetch 3-day weather forecast.");
}

const forecast = await forecastResponse.json();
setForecastData(forecast);
console.log("3-Day Forecast Data:", forecast); 
    } catch (err) {
      setError(
        "Backend connection failed. Make sure the Flask server is running."
      );
      setWeatherData(null);
    } finally {
      setLoading(false);
    }
  };
const getDailyForecast = () => {
  if (!forecastData?.forecast) return [];

  const { time, temperature, precipitation, humidity } = forecastData.forecast;

  const dailyData = {};

  time.forEach((dateTime, index) => {
    const date = dateTime.split("T")[0];

    if (!dailyData[date]) {
      dailyData[date] = {
        date,
        temperatures: [],
        precipitation: [],
        humidity: [],
      };
    }

    dailyData[date].temperatures.push(temperature[index]);
    dailyData[date].precipitation.push(precipitation[index]);
    dailyData[date].humidity.push(humidity[index]);
  });

  return Object.values(dailyData)
    .slice(0, 3)
    .map((day) => ({
      date: day.date,
      maxTemp: Math.max(...day.temperatures).toFixed(1),
      minTemp: Math.min(...day.temperatures).toFixed(1),
      rainfall: day.precipitation
        .reduce((sum, value) => sum + (value || 0), 0)
        .toFixed(1),
      humidity: Math.round(
        day.humidity.reduce((sum, value) => sum + (value || 0), 0) /
          day.humidity.length
      ),
    }));
};

const dailyForecast = getDailyForecast();
const risk = weatherData?.prediction?.flood_risk || "UNKNOWN";
  const confidence = weatherData?.prediction?.confidence_percent ?? 0;

  const riskClass =
    risk === "HIGH"
      ? "risk-high"
      : risk === "MEDIUM"
      ? "risk-medium"
      : risk === "LOW"
      ? "risk-low"
      : "risk-unknown";

  return (
    <div className="app">
      {/* Header */}

      <header className="header">
        <div className="brand">
          <div className="brand-icon">
            <CloudRain size={30} />
          </div>

          <div>
            <h1>Local Weather & Flood Risk</h1>
            <p>AI-Powered Weather Monitoring & Flood Risk Prediction</p>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          AI System Active
        </div>
      </header>

      <main className="dashboard">
        {/* Hero Section */}

        <section className="hero-section">
          <div className="hero-content">
            <span className="hero-badge">
              <ShieldAlert size={16} />
              AI Flood Risk Intelligence
            </span>

            <h2>
              Know the weather.
              <br />
              <span>Understand the risk.</span>
            </h2>

            <p>
              Real-time weather monitoring combined with machine learning to
              estimate rainfall-based flood risk for your selected location.
            </p>
          </div>

          <div className="hero-visual">
            <Waves size={110} />
          </div>
        </section>

        {/* Location Search */}

        <section className="search-card">
          <div className="section-title">
            <MapPin size={21} />

            <div>
              <h3>Check Flood Risk</h3>
              <p>
                Search for a city or use coordinates to analyze current
                conditions.
              </p>
            </div>
          </div>

          {/* City Search */}

          <div className="city-search-section">
            <label>City / Location</label>

            <div className="city-search-row">
              <div className="input-box city-input">
                <MapPin size={18} />

                <input
                  type="text"
                  value={city}
                  onChange={(e) => {
                    setCity(e.target.value);
                    setSelectedLocation("");
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      searchCity();
                    }
                  }}
                  placeholder="Search city e.g. Lucknow"
                />
              </div>

              <button
                className="location-search-button"
                onClick={searchCity}
                disabled={searchingLocation}
              >
                {searchingLocation ? (
                  <>
                    <LoaderCircle className="spinner" size={18} />
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

            {selectedLocation && (
              <div className="selected-location-message">
                <MapPin size={16} />
                Selected: <strong>{selectedLocation}</strong>
              </div>
            )}

            {locationResults.length > 0 && (
              <div className="location-results">
                {locationResults.map((place, index) => (
                  <button
                    type="button"
                    className="location-result-item"
                    key={`${place.latitude}-${place.longitude}-${index}`}
                    onClick={() => chooseLocation(place)}
                  >
                    <MapPin size={18} />

                    <div>
                      <strong>{place.name}</strong>

                      <span>
                        {[place.district, place.state, place.country]
                          .filter(Boolean)
                          .join(", ")}
                      </span>

                      <small>
                        {place.latitude}, {place.longitude}
                      </small>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Coordinates */}

          <div className="search-controls">
            <div className="input-group">
              <label>Latitude</label>

              <div className="input-box">
                <Navigation size={18} />

                <input
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={(e) => {
                    setLatitude(e.target.value);
                    setSelectedLocation("");
                  }}
                  placeholder="Enter latitude"
                />
              </div>
            </div>

            <div className="input-group">
              <label>Longitude</label>

              <div className="input-box">
                <Navigation size={18} />

                <input
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={(e) => {
                    setLongitude(e.target.value);
                    setSelectedLocation("");
                  }}
                  placeholder="Enter longitude"
                />
              </div>
            </div>

            <button
              className="analyze-button"
              onClick={getFloodRisk}
              disabled={loading}
            >
              {loading ? (
                <>
                  <LoaderCircle className="spinner" size={19} />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search size={19} />
                  Analyze Risk
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="error-message">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}
        </section>

        {!weatherData ? (
          /* Initial State */

          <section className="welcome-card">
            <div className="welcome-icon">
              <CloudRain size={48} />
            </div>

            <h3>Weather Intelligence Ready</h3>

            <p>
              Search for a city above or enter coordinates, then click
              <strong> Analyze Risk</strong> to view live weather conditions
              and AI-assisted flood-risk analysis.
            </p>
          </section>
        ) : (
          <>
            {/* Location */}

            <section className="location-row">
              <div>
                <p className="eyebrow">CURRENT ANALYSIS</p>

                <h2>
                  <MapPin size={24} />
                  {selectedLocation || "Selected Location"}
                </h2>
              </div>

              <div className="coordinates">
                {weatherData.location?.latitude?.toFixed?.(4) ??
                  weatherData.location?.latitude}
                ,{" "}
                {weatherData.location?.longitude?.toFixed?.(4) ??
                  weatherData.location?.longitude}
              </div>
            </section>

            {/* Main Metrics */}

            <section className="metrics-grid">
              <article className="metric-card">
                <div className="metric-icon temperature">
                  <Thermometer size={25} />
                </div>

                <div>
                  <p>Temperature</p>

                  <h3>
                    {weatherData.weather_conditions?.current_temperature_c ??
                      "--"}
                    °C
                  </h3>

                  <span>Current temperature</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon humidity">
                  <Droplets size={25} />
                </div>

                <div>
                  <p>Humidity</p>

                  <h3>
                    {weatherData.weather_conditions
                      ?.current_humidity_percent ?? "--"}
                    %
                  </h3>

                  <span>Relative humidity</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon rainfall">
                  <CloudRain size={25} />
                </div>

                <div>
                  <p>Current Rain</p>

                  <h3>
                    {weatherData.weather_conditions?.current_rain_mm ?? "--"} mm
                  </h3>

                  <span>Live rainfall</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon intensity">
                  <Wind size={25} />
                </div>

                <div>
                  <p>Max Hourly Rain</p>

                  <h3>
                    {weatherData.rainfall_analysis?.maximum_hourly_rain_mm ??
                      "--"}{" "}
                    mm
                  </h3>

                  <span>Rainfall intensity</span>
                </div>
              </article>
            <article className="metric-card">
  <div className="metric-icon elevation">
    <Navigation size={25} />
  </div>

  <div>
    <p>Elevation</p>

    <h3>
      {weatherData.weather_conditions?.elevation_m ?? "--"} m
    </h3>

    <span>Terrain elevation</span>
  </div>
</article>  
            </section>

            {/* Risk + Rainfall */}

            <section className="analysis-grid">
              <article className={`risk-card ${riskClass}`}>
                <div className="risk-header">
                  <div>
                    <p className="eyebrow">AI PREDICTION</p>
                    <h3>Flood Risk Level</h3>
                  </div>

                  <ShieldAlert size={34} />
                </div>

                <div className="risk-level">{risk}</div>

                <div className="confidence-section">
                  <div className="confidence-row">
                    <span>Model confidence</span>
                    <strong>{confidence}%</strong>
                  </div>

                  <div className="confidence-track">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${Math.min(Number(confidence) || 0, 100)}%`,
                      }}
                    ></div>
                  </div>
                </div>

                <p className="model-name">
                  Model: {weatherData.prediction?.model || "Random Forest"}
                </p>
              </article>

              <article className="rainfall-card">
                <div className="section-title">
                  <CloudRain size={22} />

                  <div>
                    <h3>Rainfall Analysis</h3>
                    <p>Forecast rainfall accumulation</p>
                  </div>
                </div>

                <div className="rainfall-stats">
                  <div>
                    <span>Next 24 Hours</span>

                    <strong>
                      {weatherData.rainfall_analysis?.next_24_hours_mm ?? "--"} mm
                    </strong>
                  </div>

                  <div>
                    <span>Next 72 Hours</span>

                    <strong>
                      {weatherData.rainfall_analysis?.next_72_hours_mm ?? "--"} mm
                    </strong>
                  </div>

                  <div>
                    <span>Peak Hourly</span>

                    <strong>
                      {weatherData.rainfall_analysis?.maximum_hourly_rain_mm ??
                        "--"}{" "}
                      mm
                    </strong>
                  </div>
                </div>
              </article>
            </section>

{dailyForecast.length > 0 && (
  <section className="forecast-section">
    <h3>3-Day Weather Forecast</h3>
    <div className="forecast-grid">
  {dailyForecast.map((day) => (
    <article className="forecast-card" key={day.date}>
      <strong>
  {new Date(`${day.date}T00:00:00`).toLocaleDateString("en-US", {
    weekday: "long",
  })}
</strong>

<span className="forecast-date">
  {new Date(`${day.date}T00:00:00`).toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
  })}
</span>

      <p>
        {day.maxTemp}°C / {day.minTemp}°C
      </p>

      <p>Rainfall: {day.rainfall} mm</p>

      <p>Humidity: {day.humidity}%</p>
    </article>
  ))}
</div>
  </section>
)}
{/* Rainfall Forecast Chart */}

<section className="rainfall-chart-section">
  <h3>3-Day Rainfall Forecast</h3>

  <div style={{ width: "100%", height: 300 }}>
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dailyForecast}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
  dataKey="date"
  tickFormatter={(date) =>
    new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
      weekday: "short",
    })
  }
/>
        <YAxis />
        <Tooltip />
        <Bar dataKey="rainfall" fill="#0f6fff" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
</section>
{/* Location & Flood Risk Map */}

<section className="risk-map-section">
  <div className="section-title">
    <MapPin size={22} />

    <div>
      <h3>Location & Flood Risk Map</h3>
      <p>Selected location with the current AI flood-risk estimate.</p>
    </div>
  </div>

  <div className="map-container">
    <MapContainer
      center={[Number(latitude), Number(longitude)]}
      zoom={11}
      style={{ height: "350px", width: "100%" }}
    >
      <MapUpdater latitude={latitude} longitude={longitude} />
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <Marker position={[Number(latitude), Number(longitude)]}>
        <Popup>
          <strong>{selectedLocation || "Selected Location"}</strong>
          <br />
          Flood Risk: {weatherData.prediction?.flood_risk || "N/A"}
        </Popup>
      </Marker>
    </MapContainer>
  </div>
</section>
            {/* Risk Factors */}

            <section className="risk-factors-card">
              <div className="section-title">
                <AlertTriangle size={22} />

                <div>
                  <h3>Detected Risk Factors</h3>
                  <p>Conditions influencing the current AI risk estimate.</p>
                </div>
              </div>

              <div className="risk-factor-list">
                {weatherData.risk_factors?.length > 0 ? (
                  weatherData.risk_factors.map((factor, index) => (
                    <div className="risk-factor" key={index}>
                      <span>{index + 1}</span>
                      <p>{factor}</p>
                    </div>
                  ))
                ) : (
                  <div className="safe-message">
                    No major rainfall-related risk factors detected.
                  </div>
                )}
              </div>
            </section>
            {/* Flood Risk Alert */}

<section className={`flood-alert flood-alert-${risk.toLowerCase()}`}>
  <AlertTriangle size={24} />

  <div>
    <h3>Flood Risk Alert</h3>

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
{/* Prediction History */}
<section className="prediction-history">
  <div className="section-title">
    <ShieldAlert size={22} />

    <div>
      <h3>Prediction History</h3>
      <p>Recent flood-risk predictions saved by the system.</p>
    </div>
  </div>

  {predictionHistory.length === 0 ? (
    <p className="history-empty">
      No prediction history available yet.
    </p>
  ) : (
    <div className="history-table-wrapper">
      <table className="history-table">
        <thead>
          <tr>
            <th>Risk</th>
            <th>Confidence</th>
            <th>24h Rain</th>
            <th>72h Rain</th>
            <th>Temp.</th>
            <th>Humidity</th>
          </tr>
        </thead>

        <tbody>
          {predictionHistory.map((item) => (
            <tr key={item.id}>
              <td>
                <span
                  className={`history-risk history-risk-${item.flood_risk.toLowerCase()}`}
                >
                  {item.flood_risk}
                </span>
              </td>

              <td>{item.confidence}%</td>
              <td>{item.rainfall_24h} mm</td>
              <td>{item.rainfall_72h} mm</td>
              <td>{item.temperature}°C</td>
              <td>{item.humidity}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )}
</section>
            {/* Disclaimer */}

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

      <footer>
        <p>
          Local Weather & Flood Risk Prediction System • AI-Assisted Weather
          Intelligence
        </p>
      </footer>
    </div>
  );
}

export default App;