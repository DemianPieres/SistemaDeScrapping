"""Funciones auxiliares: extracción de coordenadas, distancias y normalización."""

from __future__ import annotations

import math
import re
from typing import Optional, Tuple
from urllib.parse import unquote

from geopy.distance import geodesic


# Patrones para extraer coordenadas de distintos formatos de URL de Google Maps.
_COORD_PATTERNS = [
    re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)"),
    re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"),
    re.compile(r"q=(-?\d+\.\d+),(-?\d+\.\d+)"),
    re.compile(r"ll=(-?\d+\.\d+),(-?\d+\.\d+)"),
    re.compile(r"center=(-?\d+\.\d+)%2C(-?\d+\.\d+)"),
]


def extract_coordinates(url: str) -> Optional[Tuple[float, float]]:
    """Extrae (lat, lng) de una URL de Google Maps. Devuelve None si no se encuentran.

    Soporta varios formatos:
    - https://www.google.com/maps/@-32.8908,-68.8272,15z
    - https://www.google.com/maps/place/...!3d-32.8908!4d-68.8272
    - https://maps.google.com/?q=-32.8908,-68.8272
    """

    if not url:
        return None
    decoded = unquote(url)
    for pattern in _COORD_PATTERNS:
        match = pattern.search(decoded)
        if match:
            try:
                lat = float(match.group(1))
                lng = float(match.group(2))
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return lat, lng
            except (TypeError, ValueError):
                continue
    return None


def haversine_km(point_a: Tuple[float, float], point_b: Tuple[float, float]) -> float:
    """Calcula la distancia en kilómetros entre dos coordenadas."""

    return geodesic(point_a, point_b).kilometers


def offset_coordinate(
    lat: float, lng: float, bearing_deg: float, distance_km: float
) -> Tuple[float, float]:
    """Desplaza una coordenada en una dirección y distancia dadas.

    Útil para construir una grilla radial alrededor del punto inicial y
    forzar a Google Maps a devolver resultados de distintas zonas.
    """

    earth_radius_km = 6371.0
    bearing = math.radians(bearing_deg)
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    angular_distance = distance_km / earth_radius_km

    new_lat = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance)
        + math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing)
    )
    new_lng = lng_rad + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat),
    )
    return math.degrees(new_lat), math.degrees(new_lng)


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    """Normaliza un teléfono a un formato compacto."""

    if not raw:
        return None
    cleaned = re.sub(r"[^\d+]", "", raw)
    return cleaned or None


def slugify(value: str) -> str:
    """Convierte un texto en un slug seguro para URLs/IDs internos."""

    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", "-", value)
    return value.strip("-")
