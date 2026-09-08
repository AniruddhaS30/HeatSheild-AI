"""
Thin async client around Open-Meteo's free, keyless APIs:
- Geocoding:  https://geocoding-api.open-meteo.com/v1/search
- Forecast:   https://api.open-meteo.com/v1/forecast
- Archive:    https://archive-api.open-meteo.com/v1/archive
"""
import asyncio
from datetime import date

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
GEOCODE_USER_AGENT = "HeatShield-AI/1.0 (heatshield@sih.internal)"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

VALID_GEO_CLASSES = {"boundary", "place"}
VALID_GEO_TYPES = {
    "administrative", "state", "city", "town", "village", "hamlet",
    "district", "county", "municipality", "suburb", "neighbourhood", "region",
}


def _format_nominatim_display(raw_query: str, item: dict) -> str:
    addr = item.get("address", {})
    country = addr.get("country") or "India"
    state = addr.get("state")

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("municipality")
    )
    district = addr.get("state_district") or addr.get("county")
    item_name = item.get("name", "").strip()

    # Determine if this search or result is for the state itself
    is_state = False
    if state:
        if raw_query.strip().lower() == state.lower() or item_name.lower() == state.lower():
            is_state = True
        elif not city and (not district or district.lower() == state.lower()):
            is_state = True

    if is_state and state:
        return f"{state}, {country}" if country else state

    primary = city or district or item_name or raw_query
    if primary.endswith(" Corporation"):
        primary = primary[:-12]

    parts = [primary]
    if state and state.lower() != primary.lower():
        parts.append(state)
    if country:
        parts.append(country)

    return ", ".join(parts)


def _format_openmeteo_display(item: dict) -> str:
    name = item.get("name", "")
    admin1 = item.get("admin1")
    country = item.get("country", "")

    parts = [name]
    if admin1 and admin1.lower() != name.lower():
        parts.append(admin1)
    if country:
        parts.append(country)
    return ", ".join(parts)

CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation"
DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,shortwave_radiation_sum,relative_humidity_2m_mean,wind_speed_10m_max"
HISTORICAL_FIELDS = "temperature_2m_max,temperature_2m_mean,relative_humidity_2m_mean"
MIN_HISTORICAL_RECORDS = 3


def daily_radiation_to_wm2(mj_per_m2: float | None) -> float:
    """Convert Open-Meteo daily shortwave_radiation_sum (MJ/m²) to mean W/m²."""
    if not mj_per_m2:
        return 0.0
    return mj_per_m2 * 1_000_000 / 86_400


class WeatherServiceError(Exception):
    pass


async def geocode_location(name: str) -> dict:
    """Resolve a free-text place name with India-first priority and clean display name."""
    clean = name.strip()
    if not clean:
        raise WeatherServiceError("Location name cannot be empty")

    headers = {"User-Agent": GEOCODE_USER_AGENT}

    # 1. India-first resolution using Nominatim with country code IN
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                NOMINATIM_GEOCODE_URL,
                params={
                    "q": clean,
                    "countrycodes": "in",
                    "format": "json",
                    "limit": 10,
                    "addressdetails": 1,
                },
                headers=headers,
            )
            if resp.status_code == 200:
                results = resp.json()
                if isinstance(results, list):
                    geo_results = [
                        r for r in results
                        if r.get("class") in VALID_GEO_CLASSES or r.get("type") in VALID_GEO_TYPES
                    ]
                    if geo_results:
                        top = geo_results[0]
                        top_name = (top.get("name") or "").lower()
                        top_state = (top.get("address", {}).get("state") or "").lower()
                        top_city = (top.get("address", {}).get("city") or "").lower()
                        query_lower = clean.lower()

                        if (
                            query_lower in top_name
                            or top_name in query_lower
                            or query_lower in top_state
                            or query_lower in top_city
                            or float(top.get("importance", 0)) >= 0.3
                        ):
                            display = _format_nominatim_display(clean, top)
                            return {
                                "name": top.get("name") or clean,
                                "display_name": display,
                                "country": top.get("address", {}).get("country", "India"),
                                "latitude": float(top["lat"]),
                                "longitude": float(top["lon"]),
                            }
    except Exception:
        pass

    # 2. Multi-result search via Open-Meteo prioritizing India
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                GEOCODE_URL,
                params={"name": clean, "count": 20, "language": "en"},
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    india_match = next(
                        (
                            r for r in results
                            if r.get("country_code", "").upper() == "IN"
                            or (r.get("country") or "").lower() == "india"
                        ),
                        None,
                    )
                    top = india_match or results[0]
                    display = _format_openmeteo_display(top)
                    return {
                        "name": top.get("name"),
                        "display_name": display,
                        "country": top.get("country"),
                        "latitude": float(top["latitude"]),
                        "longitude": float(top["longitude"]),
                    }
    except httpx.HTTPError as e:
        raise WeatherServiceError(f"Location provider error: {e}") from e
    except Exception:
        pass

    # 3. Global Nominatim fallback for non-Indian searches
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                NOMINATIM_GEOCODE_URL,
                params={
                    "q": clean,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                },
                headers=headers,
            )
            if resp.status_code == 200:
                results = resp.json()
                if results and isinstance(results, list):
                    top = results[0]
                    display = _format_nominatim_display(clean, top)
                    return {
                        "name": top.get("name") or clean,
                        "display_name": display,
                        "country": top.get("address", {}).get("country"),
                        "latitude": float(top["lat"]),
                        "longitude": float(top["lon"]),
                    }
    except Exception:
        pass

    raise WeatherServiceError(f"Could not find location '{clean}'")


async def fetch_current_weather(lat: float, lon: float) -> dict:
    """Live current conditions: temp, humidity, wind, solar radiation."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_FIELDS,
        "wind_speed_unit": "ms",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    current = data.get("current", {})
    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "solar_radiation": current.get("shortwave_radiation") or 0.0,
        "time": current.get("time"),
    }


async def fetch_current_weather_batch(points: list[tuple[float, float]]) -> list[dict | None]:
    """Fetch current weather for multiple coordinates with one shared client."""
    async def _fetch(client: httpx.AsyncClient, lat: float, lon: float) -> dict | None:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": CURRENT_FIELDS,
            "wind_speed_unit": "ms",
            "timezone": "auto",
        }
        try:
            resp = await client.get(FORECAST_URL, params=params)
            resp.raise_for_status()
            current = resp.json().get("current", {})
            if current.get("temperature_2m") is None:
                return None
            return {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "solar_radiation": current.get("shortwave_radiation") or 0.0,
                "time": current.get("time"),
            }
        except httpx.HTTPError:
            return None

    async with httpx.AsyncClient(timeout=10) as client:
        return await asyncio.gather(*[_fetch(client, lat, lon) for lat, lon in points])


async def fetch_forecast(lat: float, lon: float, days: int = 5) -> list[dict]:
    """5-day daily forecast: max/min temp, radiation, humidity, wind."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": DAILY_FIELDS,
        "forecast_days": days,
        "wind_speed_unit": "ms",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    daily = data.get("daily", {})
    out = []
    for i, d in enumerate(daily.get("time", [])):
        out.append({
            "date": d,
            "max_temp": daily["temperature_2m_max"][i],
            "min_temp": daily["temperature_2m_min"][i],
            "solar_radiation": daily_radiation_to_wm2(
                (daily.get("shortwave_radiation_sum") or [0] * (i + 1))[i]
            ),
            "humidity": (daily.get("relative_humidity_2m_mean") or [50] * (i + 1))[i],
            "wind_speed": (daily.get("wind_speed_10m_max") or [2] * (i + 1))[i],
        })
    return out


async def fetch_historical_baseline(lat: float, lon: float, target_date: date, years_back: int = 5) -> dict:
    """
    Average same-calendar-day weather over the past N years.

    Each archive request covers exactly the target month/day in one previous
    year. A minimum of three valid years is required so a partial archive
    response does not produce a misleading baseline.
    """
    md = target_date.strftime("%m-%d")

    async def _one_year(client: httpx.AsyncClient, year: int) -> dict | None:
        try:
            day = date.fromisoformat(f"{year}-{md.split('-')[0]}-{md.split('-')[1]}")
        except ValueError:
            return None  # e.g. Feb 29 in a non-leap year
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "daily": HISTORICAL_FIELDS,
            "timezone": "auto",
        }
        resp = await client.get(ARCHIVE_URL, params=params)
        if resp.status_code != 200:
            return None
        daily = resp.json().get("daily", {})
        max_temps = daily.get("temperature_2m_max", [])
        mean_temps = daily.get("temperature_2m_mean", [])
        humidity = daily.get("relative_humidity_2m_mean", [])
        if not max_temps or max_temps[0] is None:
            return None
        return {
            "max_temperature": max_temps[0],
            "mean_temperature": mean_temps[0] if mean_temps else None,
            "humidity": humidity[0] if humidity and humidity[0] is not None else None,
        }

    years = [target_date.year - y for y in range(1, years_back + 1)]
    async with httpx.AsyncClient(timeout=15) as client:
        results = await asyncio.gather(*[_one_year(client, year) for year in years])
    records = [record for record in results if record is not None]

    if len(records) < MIN_HISTORICAL_RECORDS:
        raise WeatherServiceError(
            f"Insufficient historical data: found {len(records)} valid years, "
            f"need at least {MIN_HISTORICAL_RECORDS}"
        )

    mean_temps = [r["mean_temperature"] for r in records if r["mean_temperature"] is not None]
    humidity_values = [r["humidity"] for r in records if r["humidity"] is not None]

    return {
        "historical_avg_max_temp": round(
            sum(r["max_temperature"] for r in records) / len(records), 1
        ),
        "historical_avg_mean_temp": round(sum(mean_temps) / len(mean_temps), 1) if mean_temps else None,
        "historical_avg_humidity": round(sum(humidity_values) / len(humidity_values), 1) if humidity_values else None,
        "years_used": len(records),
    }
