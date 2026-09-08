from fastapi import APIRouter, HTTPException

from app.schemas import HeatMapResponse
from app.services.heatmap import SAMPLING_NOTE, analyze_heat_map
from app.services.location import resolve_place

router = APIRouter(prefix="/api/heat-map", tags=["heat-map"])


@router.get("", response_model=HeatMapResponse)
async def get_heat_map(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
):
    display_name, center_lat, center_lon = await resolve_place(location, lat, lon)
    try:
        points = await analyze_heat_map(center_lat, center_lon)
    except Exception as error:
        raise HTTPException(502, f"Heat-map weather provider error: {error}") from error

    return HeatMapResponse(
        location=display_name,
        center={"latitude": center_lat, "longitude": center_lon},
        sampling_note=SAMPLING_NOTE,
        points=points,
    )