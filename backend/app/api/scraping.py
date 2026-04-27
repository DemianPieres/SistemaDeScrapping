"""Endpoints para iniciar y consultar jobs de scraping."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models import ScrapingJob, ScrapingJobStatus, User
from app.schemas.scraping import ScrapingJobCreate, ScrapingJobOut
from app.services.job_runner import run_scraping_job
from app.utils.database import get_db
from app.utils.helpers import extract_coordinates

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/jobs", response_model=ScrapingJobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: ScrapingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScrapingJobOut:
    """Crea un job de scraping y lo lanza en segundo plano."""

    coords = extract_coordinates(payload.source_url)
    if not coords:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La URL provista no contiene coordenadas reconocibles. "
                "Abrí Google Maps, centrá la zona deseada y copiá la URL del navegador."
            ),
        )

    job = ScrapingJob(
        owner_id=current_user.id,
        source_url=payload.source_url,
        keyword=payload.keyword,
        radius_km=payload.radius_km,
        latitude=coords[0],
        longitude=coords[1],
        status=ScrapingJobStatus.PENDING,
        config={
            "max_results": payload.max_results,
            "analyze_websites": payload.analyze_websites,
        },
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_scraping_job, job.id, payload.analyze_websites)

    return ScrapingJobOut.model_validate(job)


@router.get("/jobs", response_model=list[ScrapingJobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 25,
) -> list[ScrapingJobOut]:
    """Lista los últimos jobs del usuario."""

    stmt = (
        select(ScrapingJob)
        .where(ScrapingJob.owner_id == current_user.id)
        .order_by(desc(ScrapingJob.created_at))
        .limit(limit)
    )
    jobs = db.execute(stmt).scalars().all()
    return [ScrapingJobOut.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=ScrapingJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScrapingJobOut:
    """Obtiene el estado de un job específico."""

    job = db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return ScrapingJobOut.model_validate(job)


@router.post("/jobs/{job_id}/cancel", response_model=ScrapingJobOut)
def cancel_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScrapingJobOut:
    """Marca un job como cancelado (best-effort: el runner verifica el estado)."""

    job = db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if job.status not in (ScrapingJobStatus.PENDING, ScrapingJobStatus.RUNNING):
        raise HTTPException(status_code=400, detail="El job ya finalizó")
    job.status = ScrapingJobStatus.CANCELLED
    db.commit()
    db.refresh(job)
    return ScrapingJobOut.model_validate(job)
