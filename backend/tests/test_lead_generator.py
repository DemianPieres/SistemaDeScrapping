"""Tests del scoring de oportunidad."""

from app.services.lead_generator import compute_opportunity
from app.services.website_analyzer import WebsiteAnalysis


def test_no_website_high_opportunity():
    result = compute_opportunity(
        has_website=False,
        rating=4.5,
        reviews_count=120,
        has_phone=True,
        has_address=True,
    )
    assert result.score >= 70
    assert any("sitio web" in reason.lower() for reason in result.reasons)
    assert result.size_tier == "mediano"


def test_modern_website_low_opportunity():
    analysis = WebsiteAnalysis(
        url="https://ejemplo.com",
        status="reachable",
        is_responsive=True,
        technologies=["React", "Tailwind"],
        seo_meta={
            "title": "Ejemplo",
            "description": "desc",
            "h1_count": 2,
            "images_without_alt": 0,
            "has_https": True,
            "has_favicon": True,
        },
        page_load_seconds=1.2,
    )
    result = compute_opportunity(
        has_website=True,
        rating=4.7,
        reviews_count=50,
        has_phone=True,
        has_address=True,
        social_links={"facebook": "x", "instagram": "y", "linkedin": "z"},
        website_analysis=analysis,
    )
    assert result.score <= 35


def test_unreachable_website_creates_opportunity():
    analysis = WebsiteAnalysis(url="https://roto.example", status="unreachable")
    result = compute_opportunity(
        has_website=True,
        rating=4.0,
        reviews_count=80,
        has_phone=True,
        has_address=True,
        website_analysis=analysis,
    )
    assert result.score >= 55
    assert any("no responde" in r.lower() for r in result.reasons)


def test_size_tiers():
    assert compute_opportunity(
        has_website=False, rating=None, reviews_count=5, has_phone=False, has_address=False
    ).size_tier == "muy_pequeño"
    assert compute_opportunity(
        has_website=False, rating=None, reviews_count=2500, has_phone=False, has_address=False
    ).size_tier == "muy_grande"
