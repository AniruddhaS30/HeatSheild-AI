# HeatShield AI

**Extreme Heatwave Early Warning and Human Thermal Stress Index**
*Smart India Hackathon 2026 — Problem Statement SIH26083*

🌐 **Live Web App:** https://heatsheild-ai-iota.vercel.app
⚙️ **Live Backend API:** https://heatsheild-ai.onrender.com
📱 **Android APK:** https://github.com/AniruddhaS30/HeatSheild-AI/releases/download/v1.0.0/HeatShieldAI.apk

---

## What This Is

Most heat warnings stop at "it is 35°C." HeatShield AI goes further — it turns raw weather data into an actionable, explainable heat-health risk assessment.

Instead of just reporting temperature, it answers:

> Given current conditions, historical deviation, duration of heat exposure, and who's affected, what's the real risk — and what should be done about it?

**This is a prototype decision-support system, not a medical prediction tool.**

---

## The Pipeline

```
Weather data (Open-Meteo)
      ↓
Human thermal stress (UTCI)
      ↓
5-day forecast analysis
      ↓
Historical weather anomaly detection
      ↓
Prolonged/consecutive dangerous heat detection
      ↓
Explainable 0–100 Heat Health Risk Score
      ↓
Vulnerability-adjusted risk (General Population, Elderly, Children, Outdoor Workers)
      ↓
Smart, targeted heat-safety interventions
      ↓
Dashboard + hyperlocal heat map
```

---

## Key Features

- **Real-time weather** via Open-Meteo (temperature, humidity, wind, solar radiation)
- **UTCI-based thermal stress** — accounts for how heat actually *feels*, not just the thermometer reading, using `pythermalcomfort`
- **Explainable 0–100 Heat Health Risk Score**, combining thermal stress, historical anomaly, and prolonged-heat signals — with a visible breakdown of *why* the score is what it is
- **5-day forecast** with predicted risk per day
- **Historical anomaly detection** — is today unusually hot compared to the last 5 years for this date?
- **Prolonged heat detection** — flags consecutive dangerous-heat days, not just single hot days
- **Vulnerability profiles** — General Population, Elderly, Children, and Outdoor Workers each get a separately weighted impact score
- **Smart interventions** — targeted, prioritized, backend-generated recommendations (not hardcoded)
- **Early Warning Status Banner** — an at-a-glance risk read for first-time users
- **Hyperlocal heat map** — samples 8 points around a city center and shows real, live risk gradient on an interactive Leaflet map
- **India-first location resolution** — free-text search for Indian cities/districts/states, resolved via Nominatim + Open-Meteo geocoding

---

## Tech Stack

**Backend**
- Python, FastAPI
- Open-Meteo (weather, forecast, historical archive, geocoding)
- `pythermalcomfort` (UTCI calculation)
- SQLAlchemy + PostgreSQL
- Deployed on Render

**Web Frontend**
- React + Vite
- Axios
- Leaflet (interactive hyperlocal heat map)
- Deployed on Vercel

**Android**
- Kotlin + Jetpack Compose
- Retrofit + OkHttp + Kotlinx Serialization
- WebView + Leaflet/OpenStreetMap (bundled locally, no Google Maps API key required)
- Consumes the same backend API — no duplicated risk logic on-device

**Reliability**
- UptimeRobot health-check pings every 5 minutes to keep the free-tier Render backend warm and prevent cold-start failures

---

## API Reference

Primary endpoint:

```
GET /api/analysis?location=<city name>
```

Example:
```
https://heatsheild-ai.onrender.com/api/analysis?location=Bengaluru
```

Also available:
- `GET /api/weather/current?location=<city>` — current weather + UTCI + risk
- `GET /api/forecast?location=<city>` — 5-day forecast
- `GET /api/historical?location=<city>` — historical anomaly comparison
- `GET /api/heat-map?location=<city>` — hyperlocal sampled risk points

---

## Running Locally

**Backend**
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## Android App

Download the latest APK from the [Releases page](../../releases/latest).

To install: enable "Install from unknown sources" on your Android device, download the APK, and install directly — no laptop or build tools required.

The Android app is a client only — all risk calculations happen server-side, so both the web and Android clients always show consistent results.

---

## Disclaimer

The vulnerability and risk components are a **prototype decision-support system**, not a medically validated diagnostic tool. HeatShield AI does not predict individual health outcomes. It provides an explainable, environmental heat-health risk estimate to support preventive decision-making by individuals and authorities.