"""Cálculo de la puntuación de oportunidad y clasificación por tamaño.

La puntuación es un entero 0-100 donde valores más altos significan
mayor oportunidad para vender un sitio web/sistema personalizado:

- 100: negocio sin sitio web alguno y con buena reputación.
-  60: tiene sitio pero es obsoleto/no responsivo o sin SEO.
-  20: ya tiene un sitio moderno y completo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.services.website_analyzer import WebsiteAnalysis


@dataclass
class OpportunityResult:
    score: int
    reasons: list[str]
    size_tier: str


def _classify_size(reviews_count: Optional[int]) -> str:
    """Clasifica el tamaño del negocio según número de reseñas en Google."""

    if reviews_count is None:
        return "desconocido"
    if reviews_count < 20:
        return "muy_pequeño"
    if reviews_count < 100:
        return "pequeño"
    if reviews_count < 500:
        return "mediano"
    if reviews_count < 2000:
        return "grande"
    return "muy_grande"


def _website_signal_score(analysis: Optional[WebsiteAnalysis]) -> tuple[int, list[str]]:
    """Devuelve (puntos, motivos) en función del análisis web.

    Mayor puntaje => mayor oportunidad.
    """

    if analysis is None or analysis.status == "missing" or not analysis.url:
        return 70, ["No tiene sitio web registrado en Google Maps"]

    reasons: list[str] = []
    score = 0

    if analysis.status == "unreachable":
        score += 55
        reasons.append("El sitio web no responde o devuelve error")
        return score, reasons

    if analysis.status == "error":
        score += 35
        reasons.append("No se pudo analizar correctamente el sitio web")

    if analysis.is_responsive is False:
        score += 25
        reasons.append("El sitio no es responsivo (mobile)")

    if analysis.seo_meta:
        if not analysis.seo_meta.get("title"):
            score += 8
            reasons.append("Falta etiqueta <title>")
        if not analysis.seo_meta.get("description"):
            score += 8
            reasons.append("Falta meta description")
        if analysis.seo_meta.get("h1_count", 0) == 0:
            score += 4
            reasons.append("No hay encabezados H1")
        if analysis.seo_meta.get("images_without_alt", 0) >= 5:
            score += 4
            reasons.append("Imágenes sin atributo alt (mal SEO)")
        if not analysis.seo_meta.get("has_https"):
            score += 6
            reasons.append("No usa HTTPS")
        if not analysis.seo_meta.get("has_favicon"):
            score += 2
            reasons.append("Sin favicon")

    load_time = analysis.page_load_seconds or 0
    if load_time > 4:
        score += 8
        reasons.append(f"Carga lenta ({load_time:.1f}s)")
    elif load_time > 2.5:
        score += 4
        reasons.append(f"Carga mejorable ({load_time:.1f}s)")

    legacy_techs = {"jQuery"}
    modern_techs = {"React", "Vue", "Angular", "Tailwind", "Next"}
    techs = set(analysis.technologies or [])
    if techs & legacy_techs and not (techs & modern_techs):
        score += 6
        reasons.append("Pila tecnológica desactualizada")
    if "WordPress" in techs:
        score += 3
        reasons.append("Hecho en WordPress (frecuentemente desactualizado)")

    # Si todo está bien: bajamos el score (poco potencial de venta)
    if score == 0:
        reasons.append("Sitio moderno, responsivo y bien posicionado")
        score = 5

    return score, reasons


def compute_opportunity(
    *,
    has_website: bool,
    rating: Optional[float],
    reviews_count: Optional[int],
    has_phone: bool,
    has_address: bool,
    social_links: Optional[dict] = None,
    website_analysis: Optional[WebsiteAnalysis] = None,
) -> OpportunityResult:
    """Calcula puntuación 0-100 y razones explicativas."""

    reasons: list[str] = []
    score = 0

    web_score, web_reasons = _website_signal_score(website_analysis if has_website else None)
    score += web_score
    reasons.extend(web_reasons)

    if rating is not None and reviews_count is not None and reviews_count >= 10:
        if rating >= 4.5:
            score += 12
            reasons.append("Excelente reputación (rating ≥ 4.5)")
        elif rating >= 4.0:
            score += 8
            reasons.append("Buena reputación (rating ≥ 4.0)")
        elif rating >= 3.0:
            score += 3
        else:
            reasons.append("Reputación baja: cliente menos atractivo")

    if reviews_count is not None:
        if reviews_count >= 200:
            score += 8
            reasons.append("Negocio activo (200+ reseñas)")
        elif reviews_count >= 50:
            score += 4

    social = social_links or {}
    social_count = len(social)
    if social_count == 0 and has_website:
        score += 4
        reasons.append("Sin presencia en redes sociales detectada")
    elif social_count >= 3:
        reasons.append("Buena presencia en redes sociales")

    if has_phone:
        score += 1
    else:
        reasons.append("Sin teléfono publicado")
    if has_address:
        score += 1

    score = max(0, min(100, score))

    return OpportunityResult(
        score=score,
        reasons=reasons,
        size_tier=_classify_size(reviews_count),
    )
