from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import weather, forecast, historical, analysis, heatmap


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="HEWS - Extreme Heatwave Early Warning System",
    description="Real-time thermal-stress-based heatwave risk API (SIH26083)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather.router)
app.include_router(forecast.router)
app.include_router(historical.router)
app.include_router(analysis.router)
app.include_router(heatmap.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "HEWS API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
