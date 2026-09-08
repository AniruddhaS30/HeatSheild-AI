"""Detection of consecutive dangerous thermal-stress days."""

MIN_CONSECUTIVE_DANGEROUS_DAYS = 2

DANGEROUS_STRESS_SEVERITY = {
    "strong heat stress": 1,
    "very strong heat stress": 2,
    "extreme heat stress": 3,
}

PROLONGED_HEAT_EXPLANATION = (
    "Prolonged exposure to dangerous thermal conditions increases cumulative "
    "heat stress and reduces recovery time."
)


def _display_severity(category: str) -> str:
    return category.title()


def _event_key(event: dict) -> tuple[int, int]:
    return event["days"], event["maximum_severity_rank"]


def detect_prolonged_heat(forecast_days: list[dict]) -> dict:
    """Return the most significant consecutive dangerous-heat period."""
    events = []
    current = []

    def finish_event() -> None:
        if len(current) < MIN_CONSECUTIVE_DANGEROUS_DAYS:
            return
        maximum_day = max(
            current,
            key=lambda day: DANGEROUS_STRESS_SEVERITY[day["stress_category"].lower()],
        )
        maximum_category = maximum_day["stress_category"].lower()
        events.append({
            "days": len(current),
            "start_date": current[0]["date"],
            "end_date": current[-1]["date"],
            "event_days": current.copy(),
            "maximum_severity": _display_severity(maximum_category),
            "maximum_severity_rank": DANGEROUS_STRESS_SEVERITY[maximum_category],
        })

    for day in forecast_days:
        category = (day.get("stress_category") or "").lower()
        if category in DANGEROUS_STRESS_SEVERITY:
            current.append(day)
        else:
            finish_event()
            current = []
    finish_event()

    if not events:
        return {
            "prolonged_heat_event": False,
            "consecutive_dangerous_days": 0,
            "event_start_date": None,
            "event_end_date": None,
            "maximum_severity": None,
            "event_days": [],
            "early_warning": "No prolonged dangerous heat event detected.",
            "risk_factors": [],
            "explanation": None,
        }

    event = max(events, key=_event_key)
    severity = event["maximum_severity"]
    duration = event["days"]
    if duration >= 4 or event["maximum_severity_rank"] >= 3:
        warning = (
            f"Critical early warning: Dangerous heat conditions are expected "
            f"to persist for {duration} consecutive days."
        )
    else:
        warning = (
            f"Warning: {severity} is expected for {duration} consecutive days."
        )

    return {
        "prolonged_heat_event": True,
        "consecutive_dangerous_days": duration,
        "event_start_date": event["start_date"],
        "event_end_date": event["end_date"],
        "maximum_severity": severity,
        "event_days": event["event_days"],
        "early_warning": warning,
        "risk_factors": [
            f"{severity} expected for {duration} consecutive days",
            f"Maximum forecast severity: {severity}",
        ],
        "explanation": PROLONGED_HEAT_EXPLANATION,
    }