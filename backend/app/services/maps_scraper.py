"""Scraper de Google Maps basado en Selenium.

Estrategia:

1. Recibe una URL de Google Maps + (opcional) una palabra clave.
2. Extrae las coordenadas del centro y construye una grilla radial de
   puntos de búsqueda alrededor para forzar a Google a devolver
   resultados de toda la zona dentro del radio configurado.
3. Para cada punto de búsqueda navega a `https://www.google.com/maps/search/<keyword>/@lat,lng,15z`
   y hace scroll dentro del listado lateral hasta llenar `max_results`.
4. Para cada negocio, hace clic, espera la apertura del panel de
   detalle y extrae nombre, categoría, dirección, teléfono, sitio web,
   horario, rating, fotos y atributos.

Notas importantes:
- Google Maps cambia su DOM con frecuencia. El extractor usa selectores
  defensivos con varias alternativas y `try/except` por bloque para no
  abortar todo el job ante un cambio menor.
- El scraping tradicional de Google Maps puede activar mecanismos
  anti-bot. Por eso aplicamos un user-agent realista, delays
  configurables y movimientos suaves.
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional
from urllib.parse import quote_plus, urlparse

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.config import settings
from app.utils.helpers import extract_coordinates, haversine_km, normalize_phone, offset_coordinate


@dataclass
class ScrapedBusiness:
    """Representación intermedia de un negocio antes de persistirse."""

    name: str
    place_id: Optional[str] = None
    google_url: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    price_level: Optional[str] = None
    opening_hours: Optional[dict] = None
    photos: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)


class GoogleMapsScraper:
    """Scraper de listados y detalles de Google Maps."""

    def __init__(
        self,
        headless: bool | None = None,
        page_timeout_seconds: int | None = None,
        request_delay_seconds: float | None = None,
    ):
        self.headless = settings.scraper_headless if headless is None else headless
        self.page_timeout = page_timeout_seconds or settings.scraper_page_timeout_seconds
        self.delay = request_delay_seconds or settings.scraper_request_delay_seconds
        self._driver: Optional[WebDriver] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __enter__(self) -> "GoogleMapsScraper":
        self._driver = self._create_driver()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:  # pragma: no cover
                pass
            self._driver = None

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------
    def _create_driver(self) -> WebDriver:
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--lang=es-AR")
        options.add_argument("--window-size=1400,900")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        if settings.chrome_binary_path:
            options.binary_location = settings.chrome_binary_path

        if settings.chromedriver_path:
            service = ChromeService(executable_path=settings.chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            try:
                driver = webdriver.Chrome(options=options)
            except WebDriverException as exc:
                logger.warning("Chrome no disponible directamente, intentando webdriver-manager: {}", exc)
                from webdriver_manager.chrome import ChromeDriverManager

                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)

        driver.set_page_load_timeout(self.page_timeout)
        driver.implicitly_wait(2)
        # Ocultar marca de webdriver
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return driver

    # ------------------------------------------------------------------
    # Pública: scraping de un área
    # ------------------------------------------------------------------
    def scrape_area(
        self,
        source_url: str,
        keyword: Optional[str] = None,
        radius_km: float = 2.0,
        max_results: int = 40,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_business_found: Optional[Callable[["ScrapedBusiness"], None]] = None,
    ) -> list[ScrapedBusiness]:
        """Devuelve los negocios encontrados en el área indicada.

        :param source_url: URL inicial de Google Maps (debe contener coords).
        :param keyword: Palabra clave de búsqueda. Si es None, se usa "negocios".
        :param radius_km: Radio en km a cubrir alrededor del centro.
        :param max_results: Tope superior aproximado de negocios devueltos.
        :param on_progress: callback `(actuales, total_estimado)`.
        :param on_business_found: callback ejecutado APENAS se obtiene cada
            negocio (permite persistir incrementalmente sin esperar a que
            termine todo el job).
        """

        if self._driver is None:
            self._driver = self._create_driver()

        center = extract_coordinates(source_url)
        if not center:
            raise ValueError(
                "No se pudieron extraer coordenadas de la URL. "
                "Asegurate de copiar la URL del mapa con el lugar centrado."
            )

        keyword = (keyword or "negocios").strip()
        results: dict[str, ScrapedBusiness] = {}

        search_points = self._build_grid(center, radius_km)
        logger.info(
            "Iniciando scraping centro={}, radio={}km, puntos_búsqueda={}, keyword={!r}",
            center,
            radius_km,
            len(search_points),
            keyword,
        )

        for point in search_points:
            if len(results) >= max_results:
                break
            try:
                listings = self._collect_listing_urls(
                    keyword=keyword,
                    lat=point[0],
                    lng=point[1],
                    needed=max_results - len(results),
                )
            except Exception as exc:
                logger.warning("Falló la recolección de listados en {}: {}", point, exc)
                continue

            for listing_url in listings:
                if len(results) >= max_results:
                    break
                key = listing_url.split("?")[0]
                if key in results:
                    continue
                try:
                    business = self._scrape_listing_detail(listing_url)
                except Exception as exc:
                    logger.warning("Error extrayendo detalle de {}: {}", listing_url, exc)
                    continue
                if not business or not business.name:
                    continue
                if business.latitude and business.longitude:
                    if haversine_km(center, (business.latitude, business.longitude)) > radius_km * 1.4:
                        continue
                results[key] = business
                if on_business_found:
                    try:
                        on_business_found(business)
                    except Exception as exc:  # pragma: no cover
                        logger.warning("on_business_found falló: {}", exc)
                if on_progress:
                    on_progress(len(results), max_results)
                time.sleep(self.delay)

            if on_progress:
                on_progress(len(results), max_results)

        logger.info("Scraping finalizado. Total encontrado: {}", len(results))
        return list(results.values())

    # ------------------------------------------------------------------
    # Grid de búsqueda radial
    # ------------------------------------------------------------------
    @staticmethod
    def _build_grid(center: tuple[float, float], radius_km: float) -> list[tuple[float, float]]:
        """Construye un conjunto pequeño de puntos para cubrir el círculo.

        Mantenemos pocos puntos para que el scraping sea ágil. Con scroll
        infinito en cada punto ya alcanzamos un buen volumen de resultados.
        """

        points: list[tuple[float, float]] = [center]
        if radius_km <= 1.5:
            extra = 4
        elif radius_km <= 4:
            extra = 6
        else:
            extra = 8
        for i in range(extra):
            bearing = (360.0 / extra) * i
            points.append(offset_coordinate(center[0], center[1], bearing, radius_km * 0.6))
        return points

    # ------------------------------------------------------------------
    # Recolección de URLs de listados
    # ------------------------------------------------------------------
    def _collect_listing_urls(
        self, keyword: str, lat: float, lng: float, needed: int
    ) -> list[str]:
        """Navega a la búsqueda y recolecta URLs de los listados visibles."""

        assert self._driver is not None
        search_url = (
            f"https://www.google.com/maps/search/{quote_plus(keyword)}/@{lat},{lng},15z?hl=es"
        )
        logger.debug("Visitando búsqueda: {}", search_url)
        self._driver.get(search_url)
        self._handle_consent_dialog()

        try:
            WebDriverWait(self._driver, self.page_timeout).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/maps/place/')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[@role='feed']")),
                )
            )
        except TimeoutException:
            logger.debug("Timeout esperando feed para {}", search_url)
            return []

        feed = self._find_listing_feed()
        seen: dict[str, None] = {}
        stagnant = 0
        max_scrolls = 12
        for _ in range(max_scrolls):
            anchors = self._driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/place/')]")
            previous = len(seen)
            for anchor in anchors:
                try:
                    href = anchor.get_attribute("href")
                except StaleElementReferenceException:
                    continue
                if href and "/maps/place/" in href and href not in seen:
                    seen[href] = None
            if len(seen) >= needed:
                break
            if not self._scroll_feed(feed):
                break
            if len(seen) == previous:
                stagnant += 1
                if stagnant >= 2:
                    break
            else:
                stagnant = 0
            time.sleep(0.5)
        return list(seen.keys())

    def _find_listing_feed(self) -> Optional[WebElement]:
        assert self._driver is not None
        candidates_xpath = [
            "//div[@role='feed']",
            "//div[contains(@aria-label, 'Resultados')]",
            "//div[contains(@aria-label, 'Results')]",
        ]
        for xp in candidates_xpath:
            try:
                el = self._driver.find_element(By.XPATH, xp)
                if el:
                    return el
            except NoSuchElementException:
                continue
        return None

    def _scroll_feed(self, feed: Optional[WebElement]) -> bool:
        """Hace scroll dentro del feed lateral. Devuelve False si no hay más."""

        assert self._driver is not None
        if feed is None:
            return False
        try:
            previous_height = self._driver.execute_script("return arguments[0].scrollHeight", feed)
            self._driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", feed
            )
            time.sleep(0.7)
            new_height = self._driver.execute_script("return arguments[0].scrollHeight", feed)
            return new_height > previous_height
        except Exception:
            return False

    def _handle_consent_dialog(self) -> None:
        """Si aparece el diálogo de consentimiento de cookies, lo acepta."""

        assert self._driver is not None
        consent_buttons = [
            "//button[.//span[contains(., 'Aceptar todo')]]",
            "//button[.//span[contains(., 'Accept all')]]",
            "//button[contains(., 'Aceptar')]",
            "//button[@aria-label='Aceptar todo']",
        ]
        for xp in consent_buttons:
            try:
                btn = self._driver.find_element(By.XPATH, xp)
                btn.click()
                time.sleep(1)
                return
            except (NoSuchElementException, WebDriverException):
                continue

    # ------------------------------------------------------------------
    # Detalle de un listado
    # ------------------------------------------------------------------
    def _scrape_listing_detail(self, listing_url: str) -> Optional[ScrapedBusiness]:
        assert self._driver is not None
        self._driver.get(listing_url)
        self._handle_consent_dialog()
        try:
            WebDriverWait(self._driver, self.page_timeout).until(
                EC.presence_of_element_located((By.XPATH, "//h1"))
            )
        except TimeoutException:
            return None

        time.sleep(0.3)
        biz = ScrapedBusiness(name="")
        biz.google_url = self._driver.current_url
        biz.place_id = self._extract_place_id(biz.google_url)

        # Coordenadas desde la URL final
        coords = extract_coordinates(biz.google_url)
        if coords:
            biz.latitude, biz.longitude = coords

        biz.name = self._safe_text("//h1") or ""

        # Categoría: botón debajo del nombre
        biz.category = self._safe_text(
            "//button[contains(@jsaction, 'category') or contains(@class, 'DkEaL')]"
        )

        # Rating + reviews (varios formatos posibles)
        rating_text = self._safe_text(
            "//div[contains(@class, 'F7nice')]//span[@aria-hidden='true']"
        )
        biz.rating = _parse_float(rating_text)

        reviews_text = self._safe_text("//div[contains(@class, 'F7nice')]//span[@aria-label]")
        if reviews_text:
            biz.reviews_count = _parse_int_from_reviews(reviews_text)
        if biz.reviews_count is None:
            alt = self._safe_text("//button[contains(@aria-label, 'reseñas') or contains(@aria-label, 'reviews')]")
            biz.reviews_count = _parse_int_from_reviews(alt or "")

        # Datos por aria-label en los botones de info (más estable)
        info_buttons = self._driver.find_elements(
            By.XPATH, "//div[contains(@class, 'rogA2c')]//button[@aria-label] | //button[@data-item-id]"
        )
        for btn in info_buttons:
            try:
                aria_label = btn.get_attribute("aria-label") or ""
                data_item = btn.get_attribute("data-item-id") or ""
            except StaleElementReferenceException:
                continue

            if data_item == "address" or "Dirección" in aria_label or "Address" in aria_label:
                biz.address = _strip_label(aria_label) or _safe_inner(btn)
            elif data_item.startswith("phone") or "Teléfono" in aria_label or "Phone" in aria_label:
                biz.phone = normalize_phone(_strip_label(aria_label) or _safe_inner(btn))
            elif data_item == "authority" or "sitio web" in aria_label.lower() or "website" in aria_label.lower():
                href = btn.get_attribute("href") or _safe_inner(btn)
                biz.website = _clean_website(href)
            elif data_item == "oh" or "horario" in aria_label.lower() or "hours" in aria_label.lower():
                biz.opening_hours = self._extract_opening_hours()

        # Si todavía no tenemos sitio web, lo intentamos con un selector alternativo
        if not biz.website:
            try:
                a = self._driver.find_element(By.XPATH, "//a[@data-item-id='authority']")
                biz.website = _clean_website(a.get_attribute("href"))
            except NoSuchElementException:
                pass

        # Descripción
        biz.description = self._safe_text(
            "//div[contains(@class, 'PYvSYb')] | //div[@aria-label='Descripción']"
        )

        # Atributos (chips)
        attribute_elements = self._driver.find_elements(
            By.XPATH,
            "//div[contains(@aria-label, 'Información') or contains(@aria-label, 'About')]//div[contains(@class, 'fontBodyMedium')]",
        )
        biz.attributes = list(
            dict.fromkeys(  # dedup preservando orden
                [el.text.strip() for el in attribute_elements if el.text and len(el.text) < 80]
            )
        )

        # Fotos: primeras URLs de elementos con background-image
        photo_elements = self._driver.find_elements(
            By.XPATH,
            "//button[@data-photo-index] | //div[contains(@class, 'RZ66Rb')]//img",
        )
        for el in photo_elements[:6]:
            try:
                src = el.get_attribute("src")
                if src and src.startswith("http"):
                    biz.photos.append(src)
                else:
                    style = el.get_attribute("style") or ""
                    match = re.search(r"url\(\"?(https?:[^\")]+)", style)
                    if match:
                        biz.photos.append(match.group(1))
            except StaleElementReferenceException:
                continue

        # Ciudad heurísticamente desde la dirección
        if biz.address:
            parts = [p.strip() for p in biz.address.split(",") if p.strip()]
            if len(parts) >= 2:
                biz.city = parts[-2] if parts[-1].isdigit() else parts[-1]

        return biz

    # ------------------------------------------------------------------
    # Helpers de extracción
    # ------------------------------------------------------------------
    def _safe_text(self, xpath: str) -> Optional[str]:
        assert self._driver is not None
        try:
            el = self._driver.find_element(By.XPATH, xpath)
            text = (el.text or "").strip()
            return text or None
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def _extract_opening_hours(self) -> Optional[dict]:
        assert self._driver is not None
        rows: dict[str, str] = {}
        try:
            tables = self._driver.find_elements(
                By.XPATH, "//table[contains(@class, 'eK4R0e')] | //div[@aria-label and contains(@class,'OqCZI')]"
            )
            for table in tables:
                items = table.find_elements(By.XPATH, ".//tr")
                for tr in items:
                    cells = tr.find_elements(By.XPATH, ".//td")
                    if len(cells) >= 2:
                        rows[cells[0].text.strip()] = cells[1].text.strip()
                if rows:
                    return rows
        except Exception:
            return None
        return rows or None

    @staticmethod
    def _extract_place_id(url: str) -> Optional[str]:
        if not url:
            return None
        match = re.search(r"!1s([^!?/]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"data=([^?&#]+)", url)
        return match.group(1)[:120] if match else None


# ----------------------------------------------------------------------
# Helpers a nivel de módulo
# ----------------------------------------------------------------------
def _safe_inner(el: WebElement) -> Optional[str]:
    try:
        return (el.text or "").strip() or None
    except StaleElementReferenceException:
        return None


def _strip_label(aria_label: str) -> Optional[str]:
    """Limpia labels tipo 'Dirección: Av. Belgrano 123' -> 'Av. Belgrano 123'."""

    if not aria_label:
        return None
    parts = aria_label.split(":", 1)
    return parts[1].strip() if len(parts) == 2 else aria_label.strip()


def _parse_float(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    cleaned = text.replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def _parse_int_from_reviews(text: str) -> Optional[int]:
    if not text:
        return None
    cleaned = text.replace(".", "").replace(",", "")
    match = re.search(r"\d+", cleaned)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            return None
    return None


def _clean_website(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if url.startswith("/url?"):  # links de redirección de Google
        match = re.search(r"[?&]q=([^&]+)", url)
        if match:
            url = match.group(1)
    parsed = urlparse(url)
    if not parsed.netloc:
        return None
    return url
