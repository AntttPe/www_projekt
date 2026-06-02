"""Geolokalizacja: odległość po krzywej Ziemi (wzór haversine)."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Odległość w kilometrach między dwoma punktami geograficznymi.

    Używamy do filtrowania hodowli „w promieniu X km" oraz do sortowania
    sugestii dopasowań. Dokładność wystarczająca dla skali kraju.
    """
    R = 6371.0  # promień Ziemi w km
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * R * asin(sqrt(a))
