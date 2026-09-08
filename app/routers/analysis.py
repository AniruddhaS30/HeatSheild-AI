from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas import (
    CurrentWeatherResponse,
    HistoricalComparisonResponse,
    HeatHealthRisk,
    SmartInterventions,
    UnifiedAnalysisResponse,
)
from app.services.anomaly import ANOMALY_THRESHOLDS_C, classify_temperature_anomaly
from app.services.forecast_analysis import build_forecast_days
from app.services.health_risk import calculate_heat_health_risk
from app.services.heatwave import detect_prolonged_heat
from app.services.location import resolve_place
from app.services.risk import score_risk
from app.services.thermal import calculate_utci
from app.services.interventions import build_smart_interventions
from app.services.vulnerability import build_vulnerability_profiles
from app.services.weather import (
    WeatherServiceError,
    fetch_current_weather,
    fetch_forecast,
    fetch_historical_baseline,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("", response_model=UnifiedAnalysisResponse)
async def get_analysis(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
):
    display_name, lat, lon = await resolve_place(location, lat, lon)
    today = date.today()
    unavailable = []

    try:
        current_raw = await fetch_current_weather(lat, lon)
    except Exception:
        current_raw = None
        unavailable.append("Current weather")

    try:
        forecast_raw = await fetch_forecast(lat, lon, days=5)
        forecast_days = build_forecast_days(forecast_raw)
    except Exception:
        forecast_raw = []
        forecast_days = []
        unavailable.append("Forecast")

    try:
        baseline = await fetch_historical_baseline(lat, lon, today)
    except Exception:
        baseline = None
        unavailable.append("Historical baseline")

    current_response = None
    stress_category = None
    current_max = forecast_raw[0]["max_temp"] if forecast_raw and forecast_raw[0]["max_temp"] is not None else None
    if current_raw and current_raw.get("temperature") is not None:
        current_thermal = calculate_utci(
            air_temp_c=current_raw["temperature"],
            humidity_pct=current_raw.get("humidity") or 0.0,
            wind_speed_ms=current_raw.get("wind_speed") or 0.0,
            solar_radiation_wm2=current_raw.get("solar_radiation") or 0.0,
        )
        stress_category = current_thermal["stress_category"]
        current_risk = score_risk(
            stress_category=stress_category,
            humidity_pct=current_raw.get("humidity") or 0.0,
            wind_speed_ms=current_raw.get("wind_speed") or 0.0,
            solar_radiation_wm2=current_raw.get("solar_radiation") or 0.0,
        )
        current_response = CurrentWeatherResponse(
            location=display_name,
            latitude=lat,
            longitude=lon,
            temperature_c=current_raw["temperature"],
            feels_like_utci_c=current_thermal["utci"],
            stress_category=stress_category,
            humidity_pct=current_raw.get("humidity") or 0.0,
            wind_speed_ms=current_raw.get("wind_speed") or 0.0,
            solar_radiation_wm2=current_raw.get("solar_radiation") or 0.0,
            risk_score=current_risk["risk_score"],
            risk_level=current_risk["risk_level"],
            risk_breakdown=current_risk["breakdown"],
            timestamp=current_raw.get("time") or datetime.now(timezone.utc).isoformat(),
        )
    else:
        unavailable.append("Current thermal stress")

    historical_response = None
    anomaly_c = None
    if baseline and current_max is not None:
        anomaly_c = round(current_max - baseline["historical_avg_max_temp"], 1)
        historical_response = HistoricalComparisonResponse(
            location=display_name,
            date=today.isoformat(),
            today_max_temp_c=current_max,
            historical_avg_max_temp_c=baseline["historical_avg_max_temp"],
            historical_baseline={
                "average_max_temperature_c": baseline["historical_avg_max_temp"],
                "average_mean_temperature_c": baseline["historical_avg_mean_temp"],
                "average_humidity_pct": baseline["historical_avg_humidity"],
                "years_used": baseline["years_used"],
            },
            deviation_c=anomaly_c,
            anomaly_category=classify_temperature_anomaly(anomaly_c),
            is_anomalous=abs(anomaly_c) >= 3.0,
            years_used=baseline["years_used"],
            risk_factors=(
                [f"Temperature is {anomaly_c:.1f}°C above the historical baseline"]
                if anomaly_c >= ANOMALY_THRESHOLDS_C["moderately_above_normal"]
                else []
            ),
        )
    else:
        unavailable.append("Historical anomaly")

    prolonged = detect_prolonged_heat([day.model_dump() for day in forecast_days]) if forecast_days else None
    if prolonged is None:
        unavailable.append("Prolonged heat detection")
    risk = calculate_heat_health_risk(stress_category, anomaly_c, prolonged)
    risk["unavailable_signals"] = sorted(set(risk["unavailable_signals"] + unavailable))
    vulnerability_profiles = build_vulnerability_profiles(risk)
    smart_interventions = build_smart_interventions(risk, prolonged, vulnerability_profiles)

    return UnifiedAnalysisResponse(
        location=display_name,
        latitude=lat,
        longitude=lon,
        current_weather=current_response,
        forecast=forecast_days,
        historical_anomaly=historical_response,
        prolonged_heat_analysis=prolonged,
        heat_health_risk=HeatHealthRisk(**risk),
        vulnerability_profiles=vulnerability_profiles,
        smart_interventions=SmartInterventions(**smart_interventions),
    )