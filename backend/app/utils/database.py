"""Configuración de SQLAlchemy y sesiones de base de datos."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _build_engine_kwargs(database_url: str) -> dict:
    """Construye argumentos del engine compatibles con SQLite y PostgreSQL."""

    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


engine = create_engine(settings.database_url, **_build_engine_kwargs(settings.database_url))

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI: provee una sesión y la cierra al finalizar."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager para usar fuera del ciclo de FastAPI (ej: jobs en background)."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas declaradas y el usuario default."""

    # Importación tardía para evitar dependencias circulares
    from app.models import business, lead, scraping_job, user  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Asegurar que el usuario default exista (se usa siempre porque no hay login)
    from app.api.deps import get_or_create_default_user  # noqa: WPS433

    with session_scope() as db:
        get_or_create_default_user(db)
