"""Endpoints informativos del usuario actual.

La app no usa autenticación: todos los pedidos operan sobre el mismo
usuario default. Este módulo se mantiene únicamente para que el frontend
muestre el nombre del equipo en el header.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Devuelve los datos del usuario default."""

    return UserOut.model_validate(current_user)
