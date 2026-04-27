"""Router raíz que monta todos los endpoints bajo /api."""

from fastapi import APIRouter

from app.api import auth, businesses, leads, scraping, stats

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(scraping.router)
api_router.include_router(businesses.router)
api_router.include_router(leads.router)
api_router.include_router(stats.router)
