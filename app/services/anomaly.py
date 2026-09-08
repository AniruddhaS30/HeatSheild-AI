"""Historical temperature anomaly calculations."""

ANOMALY_THRESHOLDS_C = {
    "below_normal": -3.0,
    "moderately_above_normal": 2.0,
    "significantly_above_normal": 4.0,
    "extremely_above_normal": 7.0,
}


def classify_temperature_anomaly(anomaly_c: float) -> str:
    """Classify a temperature difference from the historical normal."""
    if anomaly_c < ANOMALY_THRESHOLDS_C["below_normal"]:
        return "Below Normal"
    if anomaly_c < ANOMALY_THRESHOLDS_C["moderately_above_normal"]:
        return "Near Normal"
    if anomaly_c < ANOMALY_THRESHOLDS_C["significantly_above_normal"]:
        return "Moderately Above Normal"
    if anomaly_c < ANOMALY_THRESHOLDS_C["extremely_above_normal"]:
        return "Significantly Above Normal"
    return "Extremely Above Normal"