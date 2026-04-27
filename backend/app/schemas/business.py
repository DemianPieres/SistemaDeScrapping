"""Esquemas Pydantic para negocios y leads."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BusinessBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None

    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    price_level: Optional[str] = None

    has_website: bool = False
    website_status: Optional[str] = None
    is_responsive: Optional[bool] = None
    detected_technologies: Optional[list[str]] = None

    opportunity_score: Optional[int] = None
    opportunity_reasons: Optional[list[str]] = None
    size_tier: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class BusinessDetail(BusinessBase):
    place_id: Optional[str] = None
    google_url: Optional[str] = None
    opening_hours: Optional[dict[str, Any]] = None
    photos: Optional[list[str]] = None
    attributes: Optional[list[str]] = None
    social_links: Optional[dict[str, str]] = None
    seo_meta: Optional[dict[str, Any]] = None
    page_load_seconds: Optional[float] = None


class BusinessFilter(BaseModel):
    category: Optional[str] = None
    city: Optional[str] = None
    min_score: Optional[int] = Field(default=None, ge=0, le=100)
    max_score: Optional[int] = Field(default=None, ge=0, le=100)
    has_website: Optional[bool] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    size_tier: Optional[str] = None
    search: Optional[str] = None


class PaginatedBusinesses(BaseModel):
    items: list[BusinessBase]
    total: int
    page: int
    size: int
