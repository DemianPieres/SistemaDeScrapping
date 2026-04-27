"""Esquemas Pydantic para los jobs de scraping."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapingJobCreate(BaseModel):
    source_url: str = Field(min_length=10, description="URL de Google Maps")
    keyword: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Palabra clave (ej: restaurantes, gimnasios)",
    )
    radius_km: float = Field(default=2.0, ge=0.2, le=20.0)
    analyze_websites: bool = True
    max_results: int = Field(default=40, ge=1, le=120)


class ScrapingJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_url: str
    keyword: Optional[str] = None
    radius_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    status: str
    progress: int
    total_found: int
    error_message: Optional[str] = None

    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


class StatsOut(BaseModel):
    total_businesses: int
    total_leads: int
    total_jobs: int
    high_opportunity_count: int
    no_website_count: int
    avg_opportunity_score: float
    by_category: list[dict]
    by_score_bucket: list[dict]
