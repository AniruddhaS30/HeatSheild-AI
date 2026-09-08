from typing import Optional
from pydantic import BaseModel


class LocationQuery(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CurrentWeatherResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_utci_c: float
    stress_category: str
    humidity_pct: float
    wind_speed_ms: float
    solar_radiation_wm2: float
    risk_score: float
    risk_level: str
    risk_breakdown: dict
    timestamp: str


class ForecastDay(BaseModel):
    date: str
    max_temp_c: float
    min_temp_c: float
    utci_prediction_c: float
    stress_category: str
    risk_level: str


class ProlongedHeatAnalysis(BaseModel):
    prolonged_heat_event: bool
    consecutive_dangerous_days: int
    event_start_date: str | None
    event_end_date: str | None
    maximum_severity: str | None
    event_days: list[ForecastDay]
    early_warning: str
    risk_factors: list[str]
    explanation: str | None


class RiskContributor(BaseModel):
    factor: str
    value: str
    contribution: float
    explanation: str


class HeatHealthRisk(BaseModel):
    score: float
    level: str
    contributors: list[RiskContributor]
    unavailable_signals: list[str]
    weights: dict[str, float]


class VulnerabilityProfile(BaseModel):
    profile: str
    base_environmental_risk: float
    base_risk_level: str
    vulnerability_multiplier: float
    vulnerability_adjustment: float
    impact_score: float
    impact_level: str
    explanation: str
    risk_factors: list[str]
    recommended_actions: list[str]


class SmartIntervention(BaseModel):
    category: str
    priority: str
    target: str
    action: str
    reason: str
    triggers: list[str]


class SmartInterventions(BaseModel):
    overall_recommendation_level: str
    summary: str
    interventions: list[SmartIntervention]


class HeatMapPoint(BaseModel):
    name: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_utci_c: float
    stress_category: str
    risk_score: float
    risk_level: str


class HeatMapResponse(BaseModel):
    location: str
    center: dict[str, float]
    sampling_note: str
    points: list[HeatMapPoint]


class ForecastResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    days: list[ForecastDay]
    prolonged_heat_event: bool
    consecutive_dangerous_days: int
    event_start_date: str | None
    event_end_date: str | None
    maximum_severity: str | None
    event_days: list[ForecastDay]
    early_warning: str
    risk_factors: list[str]
    explanation: str | None
    prolonged_heat_analysis: ProlongedHeatAnalysis


class HistoricalComparisonResponse(BaseModel):
    location: str
    date: str
    today_max_temp_c: float
    historical_avg_max_temp_c: float
    historical_baseline: dict
    deviation_c: float
    anomaly_category: str
    is_anomalous: bool
    years_used: int
    risk_factors: list[str]


class UnifiedAnalysisResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    current_weather: CurrentWeatherResponse | None
    forecast: list[ForecastDay]
    historical_anomaly: HistoricalComparisonResponse | None
    prolonged_heat_analysis: ProlongedHeatAnalysis | None
    heat_health_risk: HeatHealthRisk
    vulnerability_profiles: list[VulnerabilityProfile]
    smart_interventions: SmartInterventions
