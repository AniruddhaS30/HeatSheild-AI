"""Transparent, configurable decision-support intervention rules."""

PRIORITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

RISK_LEVEL_RULES = {
    "LOW": {
        "priority": "LOW",
        "category": "PUBLIC_SAFETY",
        "target": "General Public",
        "action": "Continue normal monitoring and maintain public heat-safety awareness.",
        "reason": "Overall Heat Health Risk is LOW.",
    },
    "MODERATE": {
        "priority": "MEDIUM",
        "category": "PUBLIC_SAFETY",
        "target": "General Public",
        "action": "Issue preventive heat-safety advisories and encourage hydration.",
        "reason": "Overall Heat Health Risk is MODERATE.",
    },
    "HIGH": {
        "priority": "HIGH",
        "category": "PUBLIC_SAFETY",
        "target": "General Public",
        "action": "Issue a public heat alert and advise people to avoid peak afternoon heat.",
        "reason": "Overall Heat Health Risk is HIGH.",
    },
    "CRITICAL": {
        "priority": "CRITICAL",
        "category": "MUNICIPAL_ACTION",
        "target": "Municipal Authorities",
        "action": "Activate the emergency heat action plan and issue urgent public alerts.",
        "reason": "Overall Heat Health Risk is CRITICAL.",
    },
}

PROFILE_RULES = {
    "ELDERLY": {
        "category": "VULNERABLE_POPULATIONS",
        "target": "Elderly residents and community services",
        "action": "Increase welfare checks and ensure elderly residents have cooling and hydration access.",
        "reason": "Elderly impact is {level} at {score:.1f}.",
    },
    "CHILDREN": {
        "category": "VULNERABLE_POPULATIONS",
        "target": "Children, families, and schools",
        "action": "Limit strenuous outdoor activity and ensure frequent hydration for children.",
        "reason": "Children impact is {level} at {score:.1f}.",
    },
    "OUTDOOR_WORKERS": {
        "category": "OUTDOOR_WORK",
        "target": "Employers and Outdoor Workers",
        "action": "Shift outdoor work away from peak afternoon heat and provide scheduled cooling breaks.",
        "reason": "Outdoor worker impact is {level} at {score:.1f}.",
    },
}


def _add_intervention(interventions: list[dict], *, category: str, priority: str,
                      target: str, action: str, reason: str, triggers: list[str]) -> None:
    interventions.append({
        "category": category,
        "priority": priority,
        "target": target,
        "action": action,
        "reason": reason,
        "triggers": triggers,
    })


def build_smart_interventions(base_risk: dict, prolonged: dict | None,
                              vulnerability_profiles: list[dict]) -> dict:
    """Build prioritized interventions from already-computed analysis signals."""
    level = base_risk.get("level", "LOW")
    score = float(base_risk.get("score", 0.0))
    interventions = []
    risk_trigger = f"Heat Health Risk: {level} ({score:.1f}/100)"

    risk_rule = RISK_LEVEL_RULES[level]
    _add_intervention(
        interventions,
        **risk_rule,
        triggers=[risk_trigger],
    )

    if level in {"HIGH", "CRITICAL"}:
        healthcare_priority = "CRITICAL" if level == "CRITICAL" else "HIGH"
        _add_intervention(
            interventions,
            category="HEALTHCARE",
            priority=healthcare_priority,
            target="Healthcare Systems",
            action="Prepare emergency departments and heat-illness response capacity.",
            reason=f"Environmental risk is {level} and may increase heat-related demand.",
            triggers=[risk_trigger],
        )

    if prolonged and prolonged.get("prolonged_heat_event"):
        days = prolonged["consecutive_dangerous_days"]
        severity = prolonged.get("maximum_severity") or "dangerous thermal stress"
        duration_trigger = f"{days} consecutive dangerous days; maximum severity: {severity}"
        _add_intervention(
            interventions,
            category="MUNICIPAL_ACTION",
            priority="CRITICAL" if level == "CRITICAL" else "HIGH",
            target="Municipal Authorities",
            action="Prepare cooling facilities and deploy interventions before the prolonged heat event peaks.",
            reason="Forecast conditions indicate persistent dangerous heat and reduced recovery time.",
            triggers=[risk_trigger, duration_trigger],
        )

    for profile in vulnerability_profiles:
        profile_name = profile["profile"]
        profile_level = profile["impact_level"]
        if profile_name not in PROFILE_RULES or profile_level not in {"HIGH", "CRITICAL"}:
            continue
        rule = PROFILE_RULES[profile_name]
        _add_intervention(
            interventions,
            category=rule["category"],
            priority="CRITICAL" if profile_level == "CRITICAL" else "HIGH",
            target=rule["target"],
            action=rule["action"],
            reason=rule["reason"].format(level=profile_level, score=profile["impact_score"]),
            triggers=[risk_trigger, f"{profile_name} impact score: {profile['impact_score']:.1f} ({profile_level})"],
        )

    interventions.sort(key=lambda intervention: PRIORITY_RANK[intervention["priority"]])
    return {
        "overall_recommendation_level": level,
        "summary": (
            f"{len(interventions)} decision-support intervention(s) generated for "
            f"{level} Heat Health Risk. Recommendations should be reviewed by responsible authorities."
        ),
        "interventions": interventions,
    }