"""Endpoints para listar/filtrar/exportar negocios."""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models import Business, ScrapingJob, User
from app.schemas.business import BusinessBase, BusinessDetail, PaginatedBusinesses
from app.utils.database import get_db

router = APIRouter(prefix="/businesses", tags=["businesses"])


def _filtered_query(
    db: Session,
    *,
    user: User,
    job_id: Optional[int],
    category: Optional[str],
    city: Optional[str],
    min_score: Optional[int],
    max_score: Optional[int],
    has_website: Optional[bool],
    min_rating: Optional[float],
    size_tier: Optional[str],
    search: Optional[str],
):
    """Construye un select aplicando los filtros provistos."""

    stmt = select(Business)

    # Restringimos a negocios pertenecientes a jobs del usuario.
    job_subq = select(ScrapingJob.id).where(ScrapingJob.owner_id == user.id)
    stmt = stmt.where(Business.scraping_job_id.in_(job_subq))

    if job_id is not None:
        stmt = stmt.where(Business.scraping_job_id == job_id)
    if category:
        stmt = stmt.where(Business.category.ilike(f"%{category}%"))
    if city:
        stmt = stmt.where(Business.city.ilike(f"%{city}%"))
    if min_score is not None:
        stmt = stmt.where(Business.opportunity_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Business.opportunity_score <= max_score)
    if has_website is True:
        stmt = stmt.where(Business.has_website.is_(True))
    elif has_website is False:
        stmt = stmt.where(Business.has_website.is_(False))
    if min_rating is not None:
        stmt = stmt.where(Business.rating >= min_rating)
    if size_tier:
        stmt = stmt.where(Business.size_tier == size_tier)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Business.name).like(like),
                func.lower(Business.address).like(like),
                func.lower(Business.category).like(like),
            )
        )
    return stmt


@router.get("", response_model=PaginatedBusinesses)
def list_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: Optional[int] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    has_website: Optional[bool] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    size_tier: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    order_by: str = Query("opportunity_score", pattern="^(opportunity_score|rating|reviews_count|created_at|name)$"),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedBusinesses:
    """Listado paginado y filtrado de negocios."""

    stmt = _filtered_query(
        db,
        user=current_user,
        job_id=job_id,
        category=category,
        city=city,
        min_score=min_score,
        max_score=max_score,
        has_website=has_website,
        min_rating=min_rating,
        size_tier=size_tier,
        search=search,
    )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    order_col = getattr(Business, order_by)
    order_clause = desc(order_col) if order_dir == "desc" else order_col
    items_stmt = stmt.order_by(order_clause).offset((page - 1) * size).limit(size)
    items = db.execute(items_stmt).scalars().all()

    return PaginatedBusinesses(
        items=[BusinessBase.model_validate(b) for b in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/map", response_model=list[BusinessBase])
def map_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: Optional[int] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    has_website: Optional[bool] = None,
    limit: int = Query(500, ge=1, le=2000),
) -> list[BusinessBase]:
    """Lista de negocios optimizada para visualizar en el mapa."""

    stmt = _filtered_query(
        db,
        user=current_user,
        job_id=job_id,
        category=None,
        city=None,
        min_score=min_score,
        max_score=None,
        has_website=has_website,
        min_rating=None,
        size_tier=None,
        search=None,
    ).where(Business.latitude.isnot(None), Business.longitude.isnot(None)).limit(limit)
    items = db.execute(stmt).scalars().all()
    return [BusinessBase.model_validate(b) for b in items]


@router.get("/{business_id}", response_model=BusinessDetail)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessDetail:
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    job = db.get(ScrapingJob, biz.scraping_job_id) if biz.scraping_job_id else None
    if job and job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return BusinessDetail.model_validate(biz)


@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: Optional[int] = None,
    min_score: Optional[int] = None,
    has_website: Optional[bool] = None,
):
    """Exporta los negocios filtrados a un CSV descargable."""

    stmt = _filtered_query(
        db,
        user=current_user,
        job_id=job_id,
        category=None,
        city=None,
        min_score=min_score,
        max_score=None,
        has_website=has_website,
        min_rating=None,
        size_tier=None,
        search=None,
    ).order_by(desc(Business.opportunity_score))
    rows = db.execute(stmt).scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "nombre",
            "categoria",
            "direccion",
            "ciudad",
            "telefono",
            "sitio_web",
            "tiene_sitio",
            "rating",
            "resenias",
            "puntaje_oportunidad",
            "tamaño",
            "estado_sitio",
            "tecnologias",
            "google_url",
        ]
    )
    for b in rows:
        writer.writerow(
            [
                b.id,
                b.name,
                b.category or "",
                b.address or "",
                b.city or "",
                b.phone or "",
                b.website or "",
                "sí" if b.has_website else "no",
                b.rating if b.rating is not None else "",
                b.reviews_count if b.reviews_count is not None else "",
                b.opportunity_score if b.opportunity_score is not None else "",
                b.size_tier or "",
                b.website_status or "",
                ", ".join(b.detected_technologies or []),
                b.google_url or "",
            ]
        )

    buffer.seek(0)
    headers = {"Content-Disposition": "attachment; filename=leadscraper_export.csv"}
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers=headers)
