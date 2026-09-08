from datetime import date

from fastapi import APIRouter, HTTPException

from app.schemas import HistoricalComparisonResponse
from app.services.location import resolve_place
from app.services.weather import fetch_forecast, fetch_historical_baseline, WeatherServiceError
from app.services.anomaly import ANOMALY_THRESHOLDS_C, classify_temperature_anomaly

router = APIRouter(prefix="/api/historical", tags=["historical"])


@router.get("", response_model=HistoricalComparisonResponse)
async def get_historical_comparison(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
):
    display_name, lat, lon = await resolve_place(location, lat, lon)
    today = date.today()

    try:
        today_forecast = await fetch_forecast(lat, lon, days=1)
        baseline = await fetch_historical_baseline(lat, lon, today)
    except WeatherServiceError as e:
        raise HTTPException(502, str(e))
    except Exception as e:
        raise HTTPException(502, f"Weather provider error: {e}")

    if not today_forecast or today_forecast[0]["max_temp"] is None:
        raise HTTPException(502, "Weather provider returned no daily max for today")

    today_max = today_forecast[0]["max_temp"]
    deviation = round(today_max - baseline["historical_avg_max_temp"], 1)
    anomaly_category = classify_temperature_anomaly(deviation)
    risk_factors = []
    if deviation >= ANOMALY_THRESHOLDS_C["moderately_above_normal"]:
        risk_factors.append(
            f"Temperature is {deviation:.1f}°C above the historical baseline"
        )

    return HistoricalComparisonResponse(
        location=display_name,
        date=today.isoformat(),
        today_max_temp_c=today_max,
        historical_avg_max_temp_c=baseline["historical_avg_max_temp"],
        historical_baseline={
            "average_max_temperature_c": baseline["historical_avg_max_temp"],
            "average_mean_temperature_c": baseline["historical_avg_mean_temp"],
            "average_humidity_pct": baseline["historical_avg_humidity"],
            "years_used": baseline["years_used"],
        },
        deviation_c=deviation,
        anomaly_category=anomaly_category,
        is_anomalous=abs(deviation) >= 3.0,
        years_used=baseline["years_used"],
        risk_factors=risk_factors,
    )
