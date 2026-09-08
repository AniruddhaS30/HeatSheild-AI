"""Transparent unified heat-health risk scoring."""

from app.services.heatwave import PROLONGED_HEAT_EXPLANATION

THERMAL_STRESS_MAX_POINTS = 50
HISTORICAL_ANOMALY_MAX_POINTS = 20
PROLONGED_HEAT_MAX_POINTS = 30
HISTORICAL_ANOMALY_FULL_RISK_C = 8.0
PROLONGED_HEAT_FULL_RISK_DAYS = 5

RISK_LEVEL_THRESHOLDS = {
    "CRITICAL": 75,
    "HIGH": 50,
    "MODERATE": 25,
}

THERMAL_STRESS_POINTS = {
    "no thermal stress": 0,
    "slight heat stress": 10,
    "moderate heat stress": 25,
    "strong heat stress": 35,
    "very strong heat stress": 45,
    "extreme heat stress": 50,
}


def _risk_level(score: float) -> str:
    if score >= RISK_LEVEL_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    if score >= RISK_LEVEL_THRESHOLDS["HIGH"]:
        return "HIGH"
    if score >= RISK_LEVEL_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    return "LOW"


def calculate_heat_health_risk(
    stress_category: str | None,
    temperature_anomaly_c: float | None,
    prolonged_heat_analysis: dict | None,
) -> dict:
    """Combine available intelligence signals into an explainable 0-100 score."""
    contributors = []
    unavailable = []

    thermal_points = THERMAL_STRESS_POINTS.get((stress_category or "").lower())
    if thermal_points is None:
        unavailable.append("Current thermal stress")
    else:
        contributors.append({
            "factor": "Thermal Stress",
            "value": stress_category,
            "contribution": thermal_points,
            "explanation": "High UTCI indicates significant thermal stress on the human body.",
        })

    anomaly_points = 0.0
    if temperature_anomaly_c is None:
        unavailable.append("Historical Anomaly")
    else:
        anomaly_points = min(
            HISTORICAL_ANOMALY_MAX_POINTS,
            max(0.0, temperature_anomaly_c / HISTORICAL_ANOMALY_FULL_RISK_C * HISTORICAL_ANOMALY_MAX_POINTS),
        )
        if anomaly_points > 0:
            contributors.append({
                "factor": "Historical Anomaly",
                "value": f"{temperature_anomaly_c:+.1f}°C above normal",
                "contribution": round(anomaly_points, 1),
                "explanation": "Current temperatures are above the historical baseline.",
            })

    duration_points = 0.0
    if prolonged_heat_analysis is None:
        unavailable.append("Prolonged Heat")
    else:
        dangerous_days = prolonged_heat_analysis.get("consecutive_dangerous_days", 0)
        if prolonged_heat_analysis.get("prolonged_heat_event"):
            duration_points = min(
                PROLONGED_HEAT_MAX_POINTS,
                dangerous_days / PROLONGED_HEAT_FULL_RISK_DAYS * PROLONGED_HEAT_MAX_POINTS,
            )
            contributors.append({
                "factor": "Prolonged Heat",
                "value": f"{dangerous_days} consecutive dangerous days",
                "contribution": round(duration_points, 1),
                "explanation": PROLONGED_HEAT_EXPLANATION,
            })

    score = round(
        min(100.0, max(0.0, (thermal_points or 0) + anomaly_points + duration_points)),
        1,
    )
    return {
        "score": score,
        "level": _risk_level(score),
        "contributors": contributors,
        "unavailable_signals": unavailable,
        "weights": {
            "thermal_stress_max_points": THERMAL_STRESS_MAX_POINTS,
            "historical_anomaly_max_points": HISTORICAL_ANOMALY_MAX_POINTS,
            "prolonged_heat_max_points": PROLONGED_HEAT_MAX_POINTS,
        },
    }