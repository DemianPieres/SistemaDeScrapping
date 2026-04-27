"""Análisis de presencia digital de un negocio.

Comprueba si el sitio web responde, si parece responsivo, qué meta-tags
tiene, intenta detectar tecnologías (CMS, frameworks) y extrae enlaces a
redes sociales. Está pensado para trabajar SIN claves de pago: usa solo
la respuesta HTTP y heurísticas sobre el HTML.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from app.config import settings


@dataclass
class WebsiteAnalysis:
    """Resultado del análisis del sitio web de un negocio."""

    url: Optional[str] = None
    status: str = "missing"  # missing | reachable | unreachable | error
    is_responsive: Optional[bool] = None
    technologies: list[str] = field(default_factory=list)
    seo_meta: dict = field(default_factory=dict)
    social_links: dict[str, str] = field(default_factory=dict)
    page_load_seconds: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status,
            "is_responsive": self.is_responsive,
            "technologies": self.technologies,
            "seo_meta": self.seo_meta,
            "social_links": self.social_links,
            "page_load_seconds": self.page_load_seconds,
        }


# Patrones para detección heurística de tecnologías por contenido HTML.
_TECH_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("WordPress", re.compile(r"/wp-(content|includes|json)/", re.IGNORECASE)),
    ("WooCommerce", re.compile(r"woocommerce", re.IGNORECASE)),
    ("Shopify", re.compile(r"cdn\.shopify\.com|shopify\.theme", re.IGNORECASE)),
    ("Wix", re.compile(r"static\.wixstatic\.com|wix\.com", re.IGNORECASE)),
    ("Squarespace", re.compile(r"static1\.squarespace\.com", re.IGNORECASE)),
    ("Joomla", re.compile(r"/components/com_|joomla", re.IGNORECASE)),
    ("Drupal", re.compile(r"sites/(default|all)/", re.IGNORECASE)),
    ("React", re.compile(r"data-reactroot|__next_data__|/_next/", re.IGNORECASE)),
    ("Vue", re.compile(r"data-v-|vue\.runtime", re.IGNORECASE)),
    ("Angular", re.compile(r"ng-version|ng-app", re.IGNORECASE)),
    ("Bootstrap", re.compile(r"bootstrap(\.min)?\.css", re.IGNORECASE)),
    ("Tailwind", re.compile(r"tailwind", re.IGNORECASE)),
    ("jQuery", re.compile(r"jquery(\.min)?\.js", re.IGNORECASE)),
    ("Google Tag Manager", re.compile(r"googletagmanager\.com", re.IGNORECASE)),
    ("Facebook Pixel", re.compile(r"connect\.facebook\.net/.+/fbevents\.js", re.IGNORECASE)),
]


_SOCIAL_HOSTS = {
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "twitter.com",
    "x": "x.com",
    "linkedin": "linkedin.com",
    "youtube": "youtube.com",
    "tiktok": "tiktok.com",
    "whatsapp": "wa.me",
}


def _normalize_url(url: str) -> str:
    """Asegura que la URL tenga esquema."""

    url = url.strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url


def _detect_responsive(html: str) -> bool:
    """Detecta heurísticamente si el sitio es responsivo.

    Buscamos un meta viewport con `width=device-width` o reglas de
    `@media` típicas de mobile-first.
    """

    if not html:
        return False
    html_lower = html.lower()
    if 'name="viewport"' in html_lower and "width=device-width" in html_lower:
        return True
    if "@media" in html_lower and ("max-width" in html_lower or "min-width" in html_lower):
        return True
    return False


def _extract_seo_meta(soup: BeautifulSoup) -> dict:
    """Extrae meta-tags relevantes para SEO."""

    meta: dict = {}
    title = soup.find("title")
    if title and title.get_text(strip=True):
        meta["title"] = title.get_text(strip=True)[:255]

    description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if description_tag and description_tag.get("content"):
        meta["description"] = description_tag["content"].strip()[:500]

    keywords_tag = soup.find("meta", attrs={"name": re.compile("^keywords$", re.I)})
    if keywords_tag and keywords_tag.get("content"):
        meta["keywords"] = keywords_tag["content"].strip()[:500]

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        meta["og_title"] = og_title["content"].strip()[:255]

    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical and canonical.get("href"):
        meta["canonical"] = canonical["href"].strip()

    meta["h1_count"] = len(soup.find_all("h1"))
    meta["images_without_alt"] = sum(1 for img in soup.find_all("img") if not img.get("alt"))
    meta["has_favicon"] = bool(soup.find("link", attrs={"rel": re.compile("icon", re.I)}))
    meta["has_https"] = False  # se rellena luego con la URL final
    return meta


def _extract_social_links(soup: BeautifulSoup, base_url: str) -> dict[str, str]:
    """Devuelve un dict con `red_social -> url` detectada en la página."""

    found: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        host = urlparse(href).netloc.lower().replace("www.", "")
        for network, signature in _SOCIAL_HOSTS.items():
            if signature in host and network not in found:
                found[network] = href
    return found


def _detect_technologies(html: str, headers: dict) -> list[str]:
    """Detecta heurísticamente tecnologías presentes en el sitio."""

    detected: set[str] = set()
    server = headers.get("Server", "")
    powered = headers.get("X-Powered-By", "")
    if "cloudflare" in server.lower():
        detected.add("Cloudflare")
    if "nginx" in server.lower():
        detected.add("Nginx")
    if "apache" in server.lower():
        detected.add("Apache")
    if "php" in powered.lower():
        detected.add("PHP")
    if "asp.net" in powered.lower():
        detected.add("ASP.NET")
    if "express" in powered.lower():
        detected.add("Express")

    for name, pattern in _TECH_SIGNATURES:
        if pattern.search(html):
            detected.add(name)

    return sorted(detected)


def analyze_website(url: Optional[str]) -> WebsiteAnalysis:
    """Analiza el sitio web indicado y devuelve un `WebsiteAnalysis`.

    Si la URL es vacía/None, devuelve `status='missing'`.
    Cualquier excepción se captura para evitar romper el job de scraping.
    """

    analysis = WebsiteAnalysis()
    if not url:
        return analysis

    target = _normalize_url(url)
    analysis.url = target

    try:
        start = time.perf_counter()
        response = requests.get(
            target,
            timeout=settings.website_analyzer_timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
            allow_redirects=True,
        )
        analysis.page_load_seconds = round(time.perf_counter() - start, 3)

        if response.status_code >= 400:
            analysis.status = "unreachable"
            return analysis

        analysis.status = "reachable"
        html = response.text or ""
        soup = BeautifulSoup(html, "lxml")

        analysis.is_responsive = _detect_responsive(html)
        analysis.seo_meta = _extract_seo_meta(soup)
        analysis.seo_meta["has_https"] = response.url.lower().startswith("https://")
        analysis.social_links = _extract_social_links(soup, response.url)
        analysis.technologies = _detect_technologies(html, response.headers)

    except requests.RequestException as exc:
        logger.warning("Sitio inalcanzable {}: {}", target, exc)
        analysis.status = "unreachable"
    except Exception as exc:  # pragma: no cover - protección extra
        logger.exception("Error inesperado analizando {}: {}", target, exc)
        analysis.status = "error"

    return analysis
