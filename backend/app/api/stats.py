"""Endpoints de estadísticas para el dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models import Business, Lead, ScrapingJob, User
from app.schemas.scraping import StatsOut
from app.utils.database import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StatsOut:
    """Devuelve métricas agregadas para el dashboard del usuario."""

    user_jobs_subq = select(ScrapingJob.id).where(ScrapingJob.owner_id == current_user.id)

    total_businesses = db.execute(
        select(func.count(Business.id)).where(Business.scraping_job_id.in_(user_jobs_subq))
    ).scalar_one()

    total_leads = db.execute(
        select(func.count(Lead.id)).where(Lead.owner_id == current_user.id)
    ).scalar_one()

    total_jobs = db.execute(
        select(func.count(ScrapingJob.id)).where(ScrapingJob.owner_id == current_user.id)
    ).scalar_one()

    high_opportunity_count = db.execute(
        select(func.count(Business.id)).where(
            Business.scraping_job_id.in_(user_jobs_subq),
            Business.opportunity_score >= 70,
        )
    ).scalar_one()

    no_website_count = db.execute(
        select(func.count(Business.id)).where(
            Business.scraping_job_id.in_(user_jobs_subq),
            Business.has_website.is_(False),
        )
    ).scalar_one()

    avg_score = db.execute(
        select(func.coalesce(func.avg(Business.opportunity_score), 0)).where(
            Business.scraping_job_id.in_(user_jobs_subq)
        )
    ).scalar_one()

    by_category_rows = db.execute(
        select(
            func.coalesce(Business.category, "Sin categoría").label("category"),
            func.count(Business.id).label("count"),
            func.coalesce(func.avg(Business.opportunity_score), 0).label("avg_score"),
        )
        .where(Business.scraping_job_id.in_(user_jobs_subq))
        .group_by(Business.category)
        .order_by(func.count(Business.id).desc())
        .limit(12)
    ).all()
    by_category = [
        {
            "category": row.category,
            "count": int(row.count),
            "avg_score": round(float(row.avg_score), 1),
        }
        for row in by_category_rows
    ]

    bucket = case(
        (Business.opportunity_score >= 80, "80-100"),
        (Business.opportunity_score >= 60, "60-79"),
        (Business.opportunity_score >= 40, "40-59"),
        (Business.opportunity_score >= 20, "20-39"),
        else_="0-19",
    )
    by_bucket_rows = db.execute(
        select(bucket.label("bucket"), func.count(Business.id).label("count"))
        .where(
            Business.scraping_job_id.in_(user_jobs_subq),
            Business.opportunity_score.isnot(None),
        )
        .group_by(bucket)
    ).all()
    by_score_bucket = [
        {"bucket": row.bucket, "count": int(row.count)} for row in by_bucket_rows
    ]

    return StatsOut(
        total_businesses=int(total_businesses),
        total_leads=int(total_leads),
        total_jobs=int(total_jobs),
        high_opportunity_count=int(high_opportunity_count),
        no_website_count=int(no_website_count),
        avg_opportunity_score=round(float(avg_score), 1),
        by_category=by_category,
        by_score_bucket=by_score_bucket,
    )
