"""Algorytm dopasowań — sugeruje pary do rozrodu.

Kryteria:
1. ten sam gatunek (`species`),
2. ta sama rasa (`breed`) — w prostej wersji; docelowo można poszerzyć,
3. płeć przeciwna,
4. dostępne do rozrodu (`available_for_breeding = True`),
5. niski inbred potomstwa (poniżej ustawionego progu),
6. blisko geograficznie (jeśli mamy współrzędne).

Zwracamy posortowaną listę kandydatów (najpierw najbezpieczniejsze
genetycznie, potem najbliższe).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.animal import Animal
from ..models.farm import Farm
from .geo import haversine_km
from .pedigree import inbreeding_coefficient


@dataclass
class MatchSuggestion:
    candidate: Animal
    inbreeding: float
    distance_km: float | None


def find_matches(
    animal: Animal,
    max_inbreeding: float = 0.0625,
    limit: int = 12,
) -> list[MatchSuggestion]:
    if not animal.available_for_breeding:
        return []

    opposite_sex = "female" if animal.sex == "male" else "male"

    candidates: list[Animal] = (
        Animal.query.join(Farm, Animal.farm_id == Farm.id)
        .filter(Animal.species == animal.species)
        .filter(Animal.breed == animal.breed)
        .filter(Animal.sex == opposite_sex)
        .filter(Animal.available_for_breeding.is_(True))
        .filter(Animal.id != animal.id)
        .all()
    )

    base_farm = animal.farm
    suggestions: list[MatchSuggestion] = []

    for c in candidates:
        f = inbreeding_coefficient(animal, c)
        if f > max_inbreeding:
            continue
        distance = None
        if (
            base_farm
            and c.farm
            and base_farm.latitude is not None
            and base_farm.longitude is not None
            and c.farm.latitude is not None
            and c.farm.longitude is not None
        ):
            distance = haversine_km(
                base_farm.latitude,
                base_farm.longitude,
                c.farm.latitude,
                c.farm.longitude,
            )
        suggestions.append(MatchSuggestion(candidate=c, inbreeding=f, distance_km=distance))

    # Sortujemy: najpierw niski inbred, potem mała odległość (None na koniec).
    suggestions.sort(
        key=lambda s: (s.inbreeding, s.distance_km if s.distance_km is not None else 1e9)
    )
    return suggestions[:limit]
