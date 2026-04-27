"""Modelo de negocio scrapeado desde Google Maps."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.utils.database import Base


class Business(Base):
    """Negocio detectado durante un job de scraping."""

    __tablename__ = "businesses"
    __table_args__ = (
        UniqueConstraint("place_id", name="uq_businesses_place_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identificadores
    place_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    google_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Datos básicos
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Geo
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)

    # Reseñas
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    price_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Información adicional
    opening_hours: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    attributes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    social_links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Análisis digital
    has_website: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    website_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_responsive: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    detected_technologies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    seo_meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    page_load_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Puntuación de oportunidad (0-100)
    opportunity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    opportunity_reasons: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Tamaño estimado calculado a partir de la cantidad de reseñas
    size_tier: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Metadatos del scraping
    scraping_job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scraping_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    scraping_job = relationship("ScrapingJob", back_populates="businesses")
    leads = relationship("Lead", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Business id={self.id} name={self.name!r}>"
