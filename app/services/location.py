from fastapi import HTTPException

from app.services.weather import geocode_location, WeatherServiceError


async def resolve_place(
    location: str | None,
    lat: float | None,
    lon: float | None,
) -> tuple[str, float, float]:
    """Return (display_name, lat, lon) from a city name or coordinates."""
    if lat is None or lon is None:
        if not location:
            raise HTTPException(400, "Provide either 'location' or both 'lat' and 'lon'")
        try:
            geo = await geocode_location(location)
        except WeatherServiceError as e:
            raise HTTPException(404, str(e))
        display = geo.get("display_name") or (f"{geo['name']}, {geo['country']}" if geo.get("country") else geo["name"])
        return display, geo["latitude"], geo["longitude"]
    return (location or f"{lat},{lon}"), lat, lon
