\# 🌦️ Local Weather \& Flood Risk Prediction System



An AI/ML-powered web application that provides location-based weather information, rainfall analysis, and estimated flood-risk assessment for selected locations.



\*\*Live Application:\*\* https://local-weather-flood-risk-1.onrender.com  

\*\*Backend API:\*\* https://local-weather-flood-risk.onrender.com  

\*\*GitHub Repository:\*\* https://github.com/Kusum-tech29/Local-Weather-Flood-Risk



\---



\## 📌 Project Overview



The Local Weather \& Flood Risk Prediction System helps users understand local weather conditions and assess potential flood risk using weather and rainfall data.



Users can search for a location or use their current location to retrieve weather information. The Flask backend processes weather-related parameters and uses a trained Random Forest machine learning model to estimate flood-risk levels.



The application also provides rainfall analysis, forecast summaries, an interactive map, prediction history, and visual analytics.



\## 🎯 Objectives



\- Provide weather information for searched locations.

\- Support current-location detection.

\- Analyze current and forecast rainfall conditions.

\- Estimate flood-risk levels using a Random Forest model.

\- Display prediction confidence and risk factors.

\- Visualize locations and nearby water features on a map.

\- Maintain prediction history for analysis.



\## ✨ Key Features



\### 1. Location Search

\- Search for locations by name.

\- Retrieve geographic coordinates.

\- Support location selection and reverse geocoding.



\### 2. Current Weather Information

\- Temperature

\- Humidity

\- Current rainfall/precipitation

\- Weather conditions



\### 3. Rainfall Analysis

\- Past 24-hour rainfall

\- Past 72-hour rainfall

\- Forecast rainfall for the next 24 and 72 hours

\- Maximum hourly rainfall analysis



\### 4. AI-Based Flood-Risk Estimation

\- Random Forest machine learning model.

\- LOW, MEDIUM, and HIGH risk categories.

\- Prediction confidence and class probabilities.

\- Risk factors and explanatory messages.



\### 5. Forecast-Based Risk Assessment



Uses forecast rainfall information and configured rainfall thresholds to provide a separate forecast-based risk category.



\### 6. Interactive Map

\- Leaflet-based map.

\- OpenStreetMap tiles.

\- Location visualization.

\- Nearby water-feature information when available.



\### 7. Prediction History and Analytics

\- Store prediction records in PostgreSQL.

\- View previous predictions.

\- Analyze prediction trends through charts.



\### 8. AI Test Mode



Provides simulated LOW, MEDIUM, and HIGH scenarios for testing the user interface. These scenarios are not actual live-weather predictions.



\### 9. Elevation Information



Retrieves elevation information using Open-Meteo with OpenTopoData as a fallback.



\---

## 🏗️ System Architecture

```text
USER
  |
  v
React + Vite Frontend
  |
  v
Flask Backend
  |
  +----------------+----------------+
  |                |                |
  v                v                v
Weather APIs   Location Search   Elevation APIs
  |                |                |
  +----------------+----------------+
                   |
                   v
          Weather Data Processing
                   |
                   v
          Random Forest ML Model
                   |
                   v
           Flood Risk Estimate
                   |
             +-----+-----+
             |           |
             v           v
       PostgreSQL DB   API Response
             |           |
             v           v
      Prediction History React Dashboard
\## 🛠️ Technology Stack



\### Frontend

\- React 19

\- Vite

\- JavaScript

\- CSS

\- React-Leaflet

\- Leaflet

\- Recharts

\- Lucide React



\### Backend

\- Python

\- Flask

\- Flask-CORS

\- Gunicorn

\- Requests

\- Python-dotenv



\### Machine Learning and Data Processing

\- Scikit-learn

\- Random Forest Classifier

\- NumPy

\- Pandas

\- Joblib



\### Database

\- Neon PostgreSQL

\- Psycopg2



\### External Services

\- Open-Meteo

\- WeatherAPI fallback

\- OpenTopoData

\- OpenStreetMap



\### Deployment

\- Render

\- GitHub



\---

\## 📂 Project Structure



```text

Local-Weather-Flood-Risk/

│

├── app.py

├── requirements.txt

├── Procfile

├── train\_model.py

├── prepare\_ml\_data.py

├── collect\_historical\_data.py

├── package.json

├── package-lock.json

│

├── data/

├── models/

├── geonames\_india/

│

├── frontend/

│   ├── src/

│   │   ├── assets/

│   │   ├── App.jsx

│   │   ├── App.css

│   │   ├── main.jsx

│   │   └── index.css

│   ├── package.json

│   └── package-lock.json

│

├── .gitignore

└── README.md

```



\---



\## ⚙️ Installation and Setup



\### Prerequisites

\- Python 3.10 or later

\- Node.js and npm

\- Git

\- Neon PostgreSQL database or another compatible PostgreSQL database



\### 1. Clone the Repository



```bash

git clone https://github.com/Kusum-tech29/Local-Weather-Flood-Risk.git

cd Local-Weather-Flood-Risk

```



\### 2. Backend Setup



Create a virtual environment:



```bash

python -m venv venv

```



Activate it on Windows PowerShell:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install Python dependencies:



```bash

pip install -r requirements.txt

```



\### 3. Configure Environment Variables



Create a `.env` file in the project root:



```env

DATABASE\_URL=your\_postgresql\_connection\_string

WEATHERAPI\_KEY=your\_weatherapi\_key

```



Never upload real API keys, database passwords, or secret credentials to GitHub.



\### 4. Start the Backend



```bash

python app.py

```



The backend normally runs at:



```text

http://127.0.0.1:5000

```



\### 5. Frontend Setup



Open another terminal and navigate to the frontend folder:



```bash

cd frontend

```



Install frontend dependencies:



```bash

npm install

```



Create `frontend/.env`:



```env

VITE\_API\_BASE\_URL=http://127.0.0.1:5000

```



Start the frontend:



```bash

npm run dev

```



Open the local URL displayed by Vite in your browser.



\## 🔌 Backend API Endpoints



| Endpoint | Method | Purpose |

|---|---|---|

| `/` | GET | Backend health/status |

| `/search-location` | GET | Location search |

| `/search-place` | GET | Place search |

| `/reverse-geocode` | GET | Coordinates to location |

| `/test-weather` | GET | Weather testing |

| `/flood-risk` | POST | Live-weather flood-risk estimate |

| `/test-flood-risk` | POST | Simulated risk testing |

| `/prediction-history` | GET | Retrieve prediction history |



\### Example Flood-Risk Request



```json

{

&#x20; "latitude": 26.83928,

&#x20; "longitude": 80.92313

}

```



\---

\## 🤖 Machine Learning Approach



The project uses a trained Random Forest classifier to estimate flood-risk categories using weather and rainfall-related input features.



\### Prediction Categories



\- LOW

\- MEDIUM

\- HIGH



\### Model Output



The application can provide:



\- Predicted risk category

\- Model confidence

\- Class probability information

\- Identified risk factors

\- Human-readable explanation



The forecast-based risk assessment is a separate component that uses configured rainfall thresholds.



\*\*Important:\*\* Model confidence is not the probability that a flood will occur. The application provides an AI-assisted estimate, not an official flood warning.



\---



\## ☁️ Deployment



The application is deployed using Render.



| Component | Deployment |

|---|---|

| Frontend | https://local-weather-flood-risk-1.onrender.com |

| Backend | https://local-weather-flood-risk.onrender.com |

| Source Code | https://github.com/Kusum-tech29/Local-Weather-Flood-Risk |



The frontend communicates with the Flask backend through the configured API base URL.



\---



\## ⚠️ Limitations



\- Prediction quality depends on the availability and accuracy of external weather data.

\- External APIs may enforce request limits.

\- Elevation and nearby-water-feature data may not always be available.

\- AI Test Mode uses simulated scenarios.

\- The model provides an estimate and cannot guarantee that flooding will or will not occur.

\- The system is not a replacement for official meteorological or disaster-management warnings.

\- Snowfall and ice-risk prediction are not currently supported.



\---



\## 🚀 Future Enhancements



\- Improve model accuracy using additional verified historical datasets.

\- Add more advanced rainfall and hydrological features.

\- Introduce notification and alert functionality.

\- Improve location-search coverage.

\- Add more detailed model evaluation and explainability.

\- Explore snowfall and ice-risk estimation.



\---



\## 👩‍💻 Author



\*\*Kusum\*\*  

B.Tech – Computer Science and Engineering (Data Science)



\---



\## 📜 Disclaimer



This project is developed for educational and research purposes. Its flood-risk outputs are AI-assisted estimates based on available weather and rainfall information. They must not be treated as official flood warnings or used as the sole basis for emergency decisions.

