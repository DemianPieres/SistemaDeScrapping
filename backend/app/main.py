"""Entrypoint de la aplicación FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import api_router
from app.config import settings
from app.utils.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando {} en modo {}", settings.app_name, settings.app_env)
    init_db()
    yield
    logger.info("Apagando {}", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API para encontrar clientes potenciales scrapeando Google Maps "
        "y analizando su presencia digital."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy"}
