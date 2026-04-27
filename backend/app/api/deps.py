"""Dependencias compartidas.

La aplicación se usa internamente por el equipo y no requiere login.
Todas las operaciones se realizan en nombre de un único usuario "default"
creado automáticamente al arrancar la app.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends

from app.models import User
from app.utils.database import get_db

DEFAULT_USER_EMAIL = "team@leadscraper.app"
DEFAULT_USER_NAME = "Equipo LeadScraper"


def get_or_create_default_user(db: Session) -> User:
    """Devuelve el usuario default; lo crea si no existe."""

    user = db.execute(select(User).where(User.email == DEFAULT_USER_EMAIL)).scalar_one_or_none()
    if user:
        return user
    user = User(
        email=DEFAULT_USER_EMAIL,
        full_name=DEFAULT_USER_NAME,
        hashed_password="not-used-no-auth",
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Dependency que entrega el usuario default a todos los endpoints."""

    return get_or_create_default_user(db)
