from fastapi import HTTPException

from app.schemas import ForecastDay
from app.services.risk import score_risk
from app.services.thermal import calculate_utci


def build_forecast_days(raw_days: list[dict]) -> list[ForecastDay]:
    """Calculate UTCI and existing risk levels for provider forecast days."""
    if not raw_days:
        raise HTTPException(502, "Weather provider returned no forecast data")

    out_days = []
    for day in raw_days:
        if day["max_temp"] is None or day["min_temp"] is None:
            raise HTTPException(502, "Weather provider returned incomplete forecast data")
        thermal = calculate_utci(
            air_temp_c=day["max_temp"],
            humidity_pct=day["humidity"] or 50.0,
            wind_speed_ms=day["wind_speed"] or 2.0,
            solar_radiation_wm2=day["solar_radiation"] or 0.0,
        )
        risk = score_risk(
            stress_category=thermal["stress_category"],
            humidity_pct=day["humidity"] or 50.0,
            wind_speed_ms=day["wind_speed"] or 2.0,
            solar_radiation_wm2=day["solar_radiation"] or 0.0,
        )
        out_days.append(ForecastDay(
            date=day["date"],
            max_temp_c=day["max_temp"],
            min_temp_c=day["min_temp"],
            utci_prediction_c=thermal["utci"],
            stress_category=thermal["stress_category"],
            risk_level=risk["risk_level"],
        ))
    return out_days