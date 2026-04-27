"""Tests para utilidades geográficas."""

from app.utils.helpers import (
    extract_coordinates,
    haversine_km,
    normalize_phone,
    offset_coordinate,
    slugify,
)


def test_extract_coordinates_classic_format():
    url = "https://www.google.com/maps/@-32.8908,-68.8272,15z"
    assert extract_coordinates(url) == (-32.8908, -68.8272)


def test_extract_coordinates_place_format():
    url = "https://www.google.com/maps/place/Mendoza/data=!3d-34.6037!4d-58.3816"
    assert extract_coordinates(url) == (-34.6037, -58.3816)


def test_extract_coordinates_query_format():
    url = "https://maps.google.com/?q=-34.6037,-58.3816"
    assert extract_coordinates(url) == (-34.6037, -58.3816)


def test_extract_coordinates_returns_none_for_invalid():
    assert extract_coordinates("https://google.com") is None
    assert extract_coordinates("") is None


def test_haversine_km_known_distance():
    # Mendoza ↔ Buenos Aires aproximadamente ~ 1000 km
    distance = haversine_km((-32.8908, -68.8272), (-34.6037, -58.3816))
    assert 950 < distance < 1100


def test_offset_coordinate_distance():
    base = (-32.8908, -68.8272)
    offset = offset_coordinate(*base, bearing_deg=90, distance_km=1)
    assert round(haversine_km(base, offset), 1) == 1.0


def test_normalize_phone_strips_non_digits():
    assert normalize_phone("(011) 4567-8910") == "01145678910"
    assert normalize_phone("+54 9 261 555-1234") == "+5492615551234"
    assert normalize_phone(None) is None


def test_slugify_handles_accents_and_spaces():
    assert slugify("Restaurante El Condimento") == "restaurante-el-condimento"
    assert slugify("CAFÉ del CENTRO!!") == "café-del-centro"
