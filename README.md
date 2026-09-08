# HEWS Backend — Day 1 (SIH26083)

Extreme Heatwave Early Warning System API. Real-time weather → UTCI thermal
stress → explainable 0-100 risk score, plus 5-day forecast and a
historical-baseline comparison.

## What's built (Day 1 checklist)

- [x] FastAPI app, CORS-ready for the Vercel frontend
- [x] `GET /api/weather/current` — live weather + UTCI + risk score
- [x] `GET /api/forecast` — 5-day forecast with UTCI/risk per day
- [x] Consecutive dangerous heat detection and early warning on the forecast response
- [x] Unified explainable heat-health risk analysis
- [x] Generalized vulnerability impact profiles with profile-specific actions
- [x] Smart prioritized intervention recommendations
- [x] Hyper-local sampled heat-risk map data
- [x] `GET /api/historical` — today vs N-year historical average, "is today anomalous?"
- [x] UTCI calculation via `pythermalcomfort` (verified against the brief's
      worked example: 39.8°C air temp → ~42-44°C feels-like, "very strong heat stress")
- [x] Risk scoring: weighted blend of UTCI category + humidity + wind + solar
      radiation, with a breakdown so the frontend can show *why* the score is what it is
- [x] SQLAlchemy models for `weather_data`, `risk_scores`, `forecast_data`
      (matches the schema in the brief), works against Postgres or local SQLite
- [x] Every endpoint accepts either `?location=Bengaluru` (auto-geocoded via
      Open-Meteo's free geocoder) or `?lat=..&lon=..`

Not built (per sprint scope — explicitly deferred): ward-level GIS, census
population weighting, intervention simulator.

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defaults to local sqlite, no edits needed to just try it
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` for interactive Swagger docs, or try:

```bash
curl "http://localhost:8000/api/weather/current?location=Bengaluru"
curl "http://localhost:8000/api/forecast?location=Bengaluru"
curl "http://localhost:8000/api/historical?location=Bengaluru"
curl "http://localhost:8000/api/analysis?location=Bengaluru"
curl "http://localhost:8000/api/heat-map?location=Bengaluru"
```

Note: this sandbox couldn't make outbound calls to Open-Meteo to test live,
so the UTCI/risk math above was verified directly against the brief's numbers.
Run the curl commands above on your machine (which has normal internet) to
confirm the live geocoding + weather fetch end to end before you deploy.

## Deploy to Render

1. Push this folder to a GitHub repo.
2. On Render: **New → Web Service**, connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **New → PostgreSQL** (free tier), copy its "Internal Database URL".
5. In the Web Service's Environment tab, set:
   - `DATABASE_URL` = the Postgres URL from step 4
   - `ALLOWED_ORIGINS` = your Vercel URL (add it after Day 2 deploy, comma-separate if more than one)
6. Deploy. Render auto-redeploys on every `git push` from here on.

## API reference

### `GET /api/weather/current`
Query: `location` (e.g. `Bengaluru`) OR `lat`+`lon`.
Returns current temp, UTCI feels-like, stress category, risk score/level, breakdown.

### `GET /api/forecast`
Query: `location` OR `lat`+`lon`, optional `days` (1-7, default 5).
Returns a list of daily max/min temp, UTCI prediction, and risk level, plus
the prolonged-heat signal. A dangerous day is one with UTCI category
`strong heat stress`, `very strong heat stress`, or `extreme heat stress`.
Two or more consecutive dangerous days form an event; if multiple events are
present, the longest event is returned, with severity used as the tie-breaker.
The existing numeric risk score is unchanged.

### `GET /api/historical`
Query: `location` OR `lat`+`lon`.
Returns today's max temp vs the average max temp on this calendar date over
the previous five years. The archive baseline also includes average daily
mean temperature and humidity when available. At least three valid historical
years are required. The response includes a temperature anomaly category:
Below Normal, Near Normal, Moderately Above Normal, Significantly Above
Normal, or Extremely Above Normal. The anomaly is exposed as a separate
explainable risk signal and does not alter the existing numeric risk score.

### `GET /api/analysis`
Returns current weather and UTCI, historical anomaly, five-day prolonged heat
analysis, and a unified explainable heat-health risk score. The score allocates
up to 50 points to current thermal stress, 20 points to a positive historical
temperature anomaly, and 30 points to prolonged dangerous heat duration.
Scores are `LOW` (0-24), `MODERATE` (25-49), `HIGH` (50-74), or `CRITICAL`
(75-100). Unavailable signals are listed in `heat_health_risk.unavailable_signals`.

The response also includes four generalized vulnerability profiles. Their
impact score is `min(100, base environmental score * profile multiplier)`.
The multipliers are 1.00 for `GENERAL_POPULATION`, 1.25 for `ELDERLY`, 1.20
for `CHILDREN`, and 1.30 for `OUTDOOR_WORKERS`. These are transparent prototype
decision-support adjustments, not medically validated predictions.

The same analysis response includes `smart_interventions`. Recommendations use
the overall risk, prolonged forecast events, and high/critical vulnerability
profiles. They are ordered `CRITICAL`, `HIGH`, `MEDIUM`, then `LOW` and are
decision-support guidance, not official government instructions.

### `GET /api/heat-map`
Returns eight representative sample points around the geocoded city center.
Each point uses live Open-Meteo current weather, the existing UTCI calculation,
and the existing environmental risk scorer. The points are intended for
prototype map visualization and are not official ward-level measurements.

## Notes / things to sanity-check with your team

- **Mean radiant temperature** isn't directly available from Open-Meteo, so
  `app/services/thermal.py` approximates it from air temp + shortwave solar
  radiation. This is a reasonable MVP stand-in, but call it out explicitly if
  judges ask about UTCI accuracy — it's not a full radiant-temperature model.
- **Risk weights** (55% thermal / 20% humidity / 10% wind / 15% solar) are a
  starting point in `app/services/risk.py` — tune them if your domain
  research suggests different weightings, and they're easy to explain in a demo.
- **Population vulnerability** is intentionally not scored yet (see sprint
  scope) — the `breakdown` dict in the risk response is structured so it's a
  clean place to add a vulnerability multiplier later without breaking the API shape.
