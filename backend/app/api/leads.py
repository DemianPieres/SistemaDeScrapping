"""Endpoints para gestionar clientes potenciales (leads)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.models import Business, Lead, LeadInteraction, ScrapingJob, User
from app.schemas.lead import InteractionCreate, InteractionOut, LeadCreate, LeadOut, LeadUpdate
from app.utils.database import get_db

router = APIRouter(prefix="/leads", tags=["leads"])


def _ensure_business_belongs_to_user(db: Session, user: User, business: Business) -> None:
    if business.scraping_job_id is None:
        return
    job = db.get(ScrapingJob, business.scraping_job_id)
    if not job or job.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")


@router.get("", response_model=list[LeadOut])
def list_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: str | None = None,
):
    stmt = (
        select(Lead)
        .where(Lead.owner_id == current_user.id)
        .options(selectinload(Lead.business), selectinload(Lead.interactions))
        .order_by(desc(Lead.updated_at))
    )
    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    leads = db.execute(stmt).scalars().all()
    return [LeadOut.model_validate(l) for l in leads]


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    business = db.get(Business, payload.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    _ensure_business_belongs_to_user(db, current_user, business)

    existing = db.execute(
        select(Lead).where(
            Lead.owner_id == current_user.id, Lead.business_id == business.id
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409, detail="Este negocio ya está en tu lista de prospectos"
        )

    lead = Lead(
        owner_id=current_user.id,
        business_id=business.id,
        notes=payload.notes,
        priority=payload.priority,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return LeadOut.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadOut:
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    if payload.status is not None:
        lead.status = payload.status
    if payload.notes is not None:
        lead.notes = payload.notes
    if payload.priority is not None:
        lead.priority = payload.priority
    db.commit()
    db.refresh(lead)
    return LeadOut.model_validate(lead)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    db.delete(lead)
    db.commit()


@router.post("/{lead_id}/interactions", response_model=InteractionOut, status_code=201)
def add_interaction(
    lead_id: int,
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InteractionOut:
    lead = db.get(Lead, lead_id)
    if not lead or lead.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    interaction = LeadInteraction(
        lead_id=lead.id,
        channel=payload.channel,
        summary=payload.summary,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return InteractionOut.model_validate(interaction)
