"""
Risk scoring: turns UTCI + raw weather factors into a 0-100 score and a
LOW/MODERATE/HIGH/CRITICAL label, with a breakdown showing why.

No census/population-vulnerability integration in the Day-1 MVP (out of
scope per the sprint plan) - this scores pure environmental thermal risk.
Population vulnerability weighting is a clean place to extend later.
"""

# UTCI stress category -> base score (0-100), per the ISB/UTCI reference scale
UTCI_BASE_SCORE = {
    "extreme cold stress": 100,
    "very strong cold stress": 90,
    "strong cold stress": 70,
    "moderate cold stress": 50,
    "slight cold stress": 30,
    "no thermal stress": 10,
    "moderate heat stress": 40,
    "strong heat stress": 65,
    "very strong heat stress": 85,
    "extreme heat stress": 100,
}

RISK_WEIGHTS = {
    "utci": 0.55,      # thermal stress is the dominant driver
    "humidity": 0.20,  # high humidity blocks sweat evaporation
    "wind": 0.10,      # low wind worsens heat retention
    "solar": 0.15,     # direct solar load
}


def _humidity_factor(humidity_pct: float) -> float:
    """0-100: higher humidity = higher risk contribution, ramps up above 40%."""
    return max(0.0, min(100.0, (humidity_pct - 20) * (100 / 60)))


def _wind_factor(wind_speed_ms: float) -> float:
    """0-100: low wind = higher risk (less evaporative cooling)."""
    return max(0.0, min(100.0, (5 - wind_speed_ms) * 20))


def _solar_factor(solar_radiation_wm2: float) -> float:
    """0-100: scales with shortwave radiation, saturating near 800 W/m2."""
    return max(0.0, min(100.0, (solar_radiation_wm2 / 800) * 100))


def score_risk(stress_category: str, humidity_pct: float,
               wind_speed_ms: float, solar_radiation_wm2: float) -> dict:
    utci_component = UTCI_BASE_SCORE.get(stress_category.lower(), 50)
    humidity_component = _humidity_factor(humidity_pct)
    wind_component = _wind_factor(wind_speed_ms)
    solar_component = _solar_factor(solar_radiation_wm2)

    weighted = (
        utci_component * RISK_WEIGHTS["utci"]
        + humidity_component * RISK_WEIGHTS["humidity"]
        + wind_component * RISK_WEIGHTS["wind"]
        + solar_component * RISK_WEIGHTS["solar"]
    )
    score = round(min(100.0, max(0.0, weighted)), 1)

    if score >= 75:
        level = "CRITICAL"
    elif score >= 55:
        level = "HIGH"
    elif score >= 35:
        level = "MODERATE"
    else:
        level = "LOW"

    breakdown = {
        "thermal_stress_pct": round(RISK_WEIGHTS["utci"] * 100),
        "humidity_pct": round(RISK_WEIGHTS["humidity"] * 100),
        "wind_pct": round(RISK_WEIGHTS["wind"] * 100),
        "solar_radiation_pct": round(RISK_WEIGHTS["solar"] * 100),
        "raw_components": {
            "utci_component": round(utci_component, 1),
            "humidity_component": round(humidity_component, 1),
            "wind_component": round(wind_component, 1),
            "solar_component": round(solar_component, 1),
        },
    }

    return {"risk_score": score, "risk_level": level, "breakdown": breakdown}
