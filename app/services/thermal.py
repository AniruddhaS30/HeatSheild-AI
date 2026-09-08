"""
Wraps pythermalcomfort's UTCI model. UTCI ("feels like" temperature) needs:
- tdb: dry bulb air temp (C)
- tr:  mean radiant temperature (C) - approximated from air temp + solar radiation
- v:   wind speed at 10m (m/s)
- rh:  relative humidity (%)
"""
from pythermalcomfort.models import utci


def estimate_mean_radiant_temp(air_temp_c: float, solar_radiation_wm2: float) -> float:
    """
    Rough approximation of mean radiant temperature from air temp + solar
    radiation, in the absence of a pyranometer/globe thermometer reading.
    Full radiant-temp models are much more involved; this is a reasonable
    stand-in for a hackathon-scale MVP and can be swapped later.
    """
    # ~0.03C of extra radiant load per W/m2 of shortwave radiation, capped at +15C
    bump = min(solar_radiation_wm2 * 0.03, 15.0)
    return air_temp_c + bump


def calculate_utci(air_temp_c: float, humidity_pct: float, wind_speed_ms: float,
                    solar_radiation_wm2: float = 0.0) -> dict:
    tr = estimate_mean_radiant_temp(air_temp_c, solar_radiation_wm2)
    # pythermalcomfort expects wind speed at 10m; clamp to its supported range
    v = max(0.0, min(wind_speed_ms, 17.0))
    rh = max(0.0, min(humidity_pct, 100.0))

    result = utci(tdb=air_temp_c, tr=tr, v=v, rh=rh, limit_inputs=False)
    category = result.stress_category
    if hasattr(category, "item"):
        category = category.item()
    return {
        "utci": round(float(result.utci), 1),
        "stress_category": str(category),
    }
