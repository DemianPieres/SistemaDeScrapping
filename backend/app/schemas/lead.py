"""Esquemas Pydantic para leads e interacciones."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.business import BusinessBase


class LeadCreate(BaseModel):
    business_id: int
    notes: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(baja|media|alta)$")


class LeadUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None,
        pattern="^(nuevo|contactado|interesado|negociando|cerrado|descartado)$",
    )
    notes: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(baja|media|alta)$")


class InteractionCreate(BaseModel):
    channel: str = Field(min_length=1, max_length=32)
    summary: str = Field(min_length=1)


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    summary: str
    occurred_at: datetime


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    notes: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    business: BusinessBase
    interactions: list[InteractionOut] = []
