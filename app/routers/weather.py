import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import WeatherData, RiskScore
from app.schemas import CurrentWeatherResponse
from app.services.location import resolve_place
from app.services.weather import fetch_current_weather
from app.services.thermal import calculate_utci
from app.services.risk import score_risk

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
):
    display_name, lat, lon = await resolve_place(location, lat, lon)

    try:
        wx = await fetch_current_weather(lat, lon)
    except Exception as e:
        raise HTTPException(502, f"Weather provider error: {e}")

    if wx["temperature"] is None:
        raise HTTPException(502, "Weather provider returned no current data")

    thermal = calculate_utci(
        air_temp_c=wx["temperature"],
        humidity_pct=wx["humidity"] or 0.0,
        wind_speed_ms=wx["wind_speed"] or 0.0,
        solar_radiation_wm2=wx["solar_radiation"] or 0.0,
    )
    risk = score_risk(
        stress_category=thermal["stress_category"],
        humidity_pct=wx["humidity"] or 0.0,
        wind_speed_ms=wx["wind_speed"] or 0.0,
        solar_radiation_wm2=wx["solar_radiation"] or 0.0,
    )

    db.add(WeatherData(
        location=display_name, latitude=lat, longitude=lon,
        temperature=wx["temperature"], humidity=wx["humidity"] or 0.0,
        wind_speed=wx["wind_speed"] or 0.0, solar_radiation=wx["solar_radiation"],
    ))
    db.add(RiskScore(
        location=display_name, utci_value=thermal["utci"],
        stress_category=thermal["stress_category"], risk_score=risk["risk_score"],
        risk_level=risk["risk_level"], breakdown=json.dumps(risk["breakdown"]),
    ))
    db.commit()

    return CurrentWeatherResponse(
        location=display_name,
        latitude=lat,
        longitude=lon,
        temperature_c=wx["temperature"],
        feels_like_utci_c=thermal["utci"],
        stress_category=thermal["stress_category"],
        humidity_pct=wx["humidity"] or 0.0,
        wind_speed_ms=wx["wind_speed"] or 0.0,
        solar_radiation_wm2=wx["solar_radiation"] or 0.0,
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        risk_breakdown=risk["breakdown"],
        timestamp=wx["time"] or datetime.now(timezone.utc).isoformat(),
    )
