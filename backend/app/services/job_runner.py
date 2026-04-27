"""Orquestador de un job de scraping.

Persiste cada negocio APENAS lo encuentra (no espera a que termine todo
el scraping). El frontend hace polling cada pocos segundos y muestra los
resultados a medida que aparecen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select

from app.models import Business, ScrapingJob, ScrapingJobStatus
from app.services.lead_generator import compute_opportunity
from app.services.maps_scraper import GoogleMapsScraper, ScrapedBusiness
from app.services.website_analyzer import WebsiteAnalysis, analyze_website
from app.utils.database import session_scope
from app.utils.helpers import extract_coordinates


def run_scraping_job(job_id: int, analyze_websites: bool = True) -> None:
    """Punto de entrada del job. Pensado para correr en background."""

    logger.info("Job {} arrancando", job_id)

    # Levantamos los parámetros del job en una sesión corta para evitar
    # mantener una conexión abierta durante todo el scraping.
    with session_scope() as db:
        job = db.get(ScrapingJob, job_id)
        if not job:
            logger.error("Job {} no encontrado", job_id)
            return
        job.status = ScrapingJobStatus.RUNNING
        job.started_at = datetime.now(tz=timezone.utc)
        job.error_message = None

        coords = extract_coordinates(job.source_url)
        if coords:
            job.latitude, job.longitude = coords

        config = job.config or {}
        max_results = int(config.get("max_results", 40))
        keyword = job.keyword
        radius = float(job.radius_km or 2.0)
        source_url = job.source_url

    def _persist(business: ScrapedBusiness) -> None:
        """Callback que guarda un negocio recién scrapeado."""

        analysis: Optional[WebsiteAnalysis] = None
        if analyze_websites and business.website:
            try:
                analysis = analyze_website(business.website)
            except Exception as exc:  # pragma: no cover - protección extra
                logger.warning("Falló el análisis web de {}: {}", business.website, exc)
        try:
            with session_scope() as db:
                _upsert_business(db, job_id, business, analysis)
        except Exception as exc:
            logger.exception("No se pudo persistir negocio {!r}: {}", business.name, exc)

    try:
        with GoogleMapsScraper() as scraper:
            results = scraper.scrape_area(
                source_url=source_url,
                keyword=keyword,
                radius_km=radius,
                max_results=max_results,
                on_progress=lambda current, total: _update_progress(job_id, current, total),
                on_business_found=_persist,
            )
        logger.info("Job {} obtuvo {} negocios", job_id, len(results))

        with session_scope() as db:
            job = db.get(ScrapingJob, job_id)
            if job:
                job.status = ScrapingJobStatus.COMPLETED
                job.finished_at = datetime.now(tz=timezone.utc)
                job.total_found = len(results)
                job.progress = 100

    except Exception as exc:
        logger.exception("Job {} falló: {}", job_id, exc)
        with session_scope() as db:
            job = db.get(ScrapingJob, job_id)
            if job:
                job.status = ScrapingJobStatus.FAILED
                job.error_message = str(exc)[:500]
                job.finished_at = datetime.now(tz=timezone.utc)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _update_progress(job_id: int, current: int, total: int) -> None:
    with session_scope() as db:
        job = db.get(ScrapingJob, job_id)
        if not job:
            return
        job.progress = min(99, int((current / max(total, 1)) * 99))
        job.total_found = current


def _upsert_business(
    db,
    job_id: int,
    business: ScrapedBusiness,
    analysis: Optional[WebsiteAnalysis],
) -> Business:
    """Inserta o actualiza un negocio identificándolo por place_id o nombre+coords."""

    existing: Optional[Business] = None
    if business.place_id:
        existing = db.execute(
            select(Business).where(Business.place_id == business.place_id)
        ).scalar_one_or_none()

    if existing is None and business.latitude and business.longitude:
        existing = db.execute(
            select(Business).where(
                Business.name == business.name,
                Business.latitude == business.latitude,
                Business.longitude == business.longitude,
            )
        ).scalar_one_or_none()

    has_website = bool(business.website)
    opportunity = compute_opportunity(
        has_website=has_website,
        rating=business.rating,
        reviews_count=business.reviews_count,
        has_phone=bool(business.phone),
        has_address=bool(business.address),
        social_links=analysis.social_links if analysis else None,
        website_analysis=analysis,
    )

    payload = {
        "place_id": business.place_id,
        "google_url": business.google_url,
        "name": business.name,
        "category": business.category,
        "address": business.address,
        "phone": business.phone,
        "website": business.website,
        "description": business.description,
        "latitude": business.latitude,
        "longitude": business.longitude,
        "city": business.city,
        "rating": business.rating,
        "reviews_count": business.reviews_count,
        "price_level": business.price_level,
        "opening_hours": business.opening_hours,
        "photos": business.photos or None,
        "attributes": business.attributes or None,
        "scraping_job_id": job_id,
        "has_website": has_website,
        "website_status": analysis.status if analysis else ("missing" if not has_website else None),
        "is_responsive": analysis.is_responsive if analysis else None,
        "detected_technologies": analysis.technologies if analysis else None,
        "seo_meta": analysis.seo_meta if analysis else None,
        "social_links": analysis.social_links if analysis else None,
        "page_load_seconds": analysis.page_load_seconds if analysis else None,
        "opportunity_score": opportunity.score,
        "opportunity_reasons": opportunity.reasons,
        "size_tier": opportunity.size_tier,
    }

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        return existing

    new_business = Business(**payload)
    db.add(new_business)
    return new_business
