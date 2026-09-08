from sqlalchemy import Column, Integer, String, Float, DateTime, func

from app.database import Base


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    solar_radiation = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True, nullable=False)
    utci_value = Column(Float, nullable=False)
    stress_category = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    breakdown = Column(String, nullable=True)  # JSON string of factor contributions
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class ForecastData(Base):
    __tablename__ = "forecast_data"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True, nullable=False)
    forecast_date = Column(String, nullable=False)
    max_temp = Column(Float, nullable=False)
    min_temp = Column(Float, nullable=False)
    utci_prediction = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
