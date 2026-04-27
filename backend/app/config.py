"""Configuración global cargada desde variables de entorno."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación.

    Los valores se leen automáticamente desde el archivo `.env` o desde
    variables de entorno. Cualquier valor sensible (como `SECRET_KEY`)
    debe sobrescribirse en producción.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aplicación
    app_name: str = "LeadScraper Argentina"
    app_env: str = "development"
    debug: bool = True

    # Seguridad
    secret_key: str = "change-me-in-production-please-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Base de datos
    database_url: str = "sqlite:///./leadscraper.db"

    # CORS (lista separada por comas en el .env)
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Scraping
    scraper_headless: bool = True
    scraper_default_radius_km: float = 2.0
    scraper_max_results_per_query: int = 40
    scraper_request_delay_seconds: float = 1.5
    scraper_page_timeout_seconds: int = 25
    chrome_binary_path: str = ""
    chromedriver_path: str = ""

    # Análisis web
    website_analyzer_timeout: int = 10


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cache) de la configuración."""

    return Settings()


settings = get_settings()
