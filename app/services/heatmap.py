"""Reusable representative sampling and real-weather heat-map analysis."""

from app.services.risk import score_risk
from app.services.thermal import calculate_utci
from app.services.weather import WeatherServiceError, fetch_current_weather_batch

SAMPLING_NOTE = (
    "Prototype hyper-local sampled locations. This is not official ward-level "
    "meteorological data."
)

# Approximate offsets in degrees around a geocoded city center. Labels are
# representative sample names, not claims about administrative boundaries.
SAMPLE_OFFSETS = (
    ("Sample North", 0.04, 0.00),
    ("Sample North-East", 0.028, 0.035),
    ("Sample East", 0.00, 0.05),
    ("Sample South-East", -0.035, 0.035),
    ("Sample South", -0.05, 0.00),
    ("Sample South-West", -0.035, -0.035),
    ("Sample West", 0.00, -0.05),
    ("Sample North-West", 0.028, -0.035),
)


def generate_sample_points(center_lat: float, center_lon: float) -> list[dict]:
    """Generate deterministic nearby coordinates around a city center."""
    return [
        {
            "name": name,
            "latitude": round(center_lat + lat_offset, 6),
            "longitude": round(center_lon + lon_offset, 6),
        }
        for name, lat_offset, lon_offset in SAMPLE_OFFSETS
    ]


async def analyze_heat_map(center_lat: float, center_lon: float) -> list[dict]:
    """Analyze each representative point using live weather and existing scoring."""
    sample_points = generate_sample_points(center_lat, center_lon)
    weather_values = await fetch_current_weather_batch([
        (point["latitude"], point["longitude"])
        for point in sample_points
    ])
    analyzed = []
    for point, weather in zip(sample_points, weather_values):
        if weather is None:
            continue
        thermal = calculate_utci(
            air_temp_c=weather["temperature"],
            humidity_pct=weather["humidity"] or 0.0,
            wind_speed_ms=weather["wind_speed"] or 0.0,
            solar_radiation_wm2=weather["solar_radiation"] or 0.0,
        )
        risk = score_risk(
            stress_category=thermal["stress_category"],
            humidity_pct=weather["humidity"] or 0.0,
            wind_speed_ms=weather["wind_speed"] or 0.0,
            solar_radiation_wm2=weather["solar_radiation"] or 0.0,
        )
        analyzed.append({
            **point,
            "temperature_c": weather["temperature"],
            "feels_like_utci_c": thermal["utci"],
            "stress_category": thermal["stress_category"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
        })

    if not analyzed:
        raise WeatherServiceError("No weather data was available for sampled locations")
    return analyzed