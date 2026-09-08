from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ForecastData
from app.schemas import ForecastResponse
from app.services.forecast_analysis import build_forecast_days
from app.services.location import resolve_place
from app.services.weather import fetch_forecast
from app.services.heatwave import detect_prolonged_heat

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("", response_model=ForecastResponse)
async def get_forecast(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    days: int = 5,
    db: Session = Depends(get_db),
):
    display_name, lat, lon = await resolve_place(location, lat, lon)

    try:
        raw_days = await fetch_forecast(lat, lon, days=min(max(days, 1), 7))
    except Exception as e:
        raise HTTPException(502, f"Weather provider error: {e}")

    out_days = build_forecast_days(raw_days)
    for raw_day, forecast_day in zip(raw_days, out_days):
        db.add(ForecastData(
            location=display_name,
            forecast_date=raw_day["date"],
            max_temp=raw_day["max_temp"],
            min_temp=raw_day["min_temp"],
            utci_prediction=forecast_day.utci_prediction_c,
            risk_level=forecast_day.risk_level,
        ))
    db.commit()
    heatwave = detect_prolonged_heat([
        day.model_dump()
        for day in out_days
    ])

    return ForecastResponse(
        location=display_name,
        latitude=lat,
        longitude=lon,
        days=out_days,
        **heatwave,
        prolonged_heat_analysis=heatwave,
    )
