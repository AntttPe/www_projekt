"""Rodowód i współczynnik inbredu.

Wzór Wrighta (kinship coefficient): inbred potomstwa pary (X, Y) to suma
wkładów po WSPÓLNYCH przodkach. Dla każdego wspólnego przodka A:

    F = Σ_A (1/2)^(n1 + n2 + 1) · (1 + F_A)

gdzie n1, n2 to długości ścieżek od X i Y do A. Zakładamy F_A = 0 jeśli
nie znamy rodziców A (typowo dla starych przodków).

Implementacja schodzi w głąb rodowodu BFS-em do `max_depth` pokoleń —
głębiej rzadko mamy dane i wkład maleje wykładniczo (0.5^n).
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.animal import Animal


def collect_ancestors(animal_id: int, max_depth: int = 4) -> dict[int, int]:
    """Zwraca dict {przodek_id: najkrótsza_odległość_w_pokoleniach}.

    Sam `animal_id` znajduje się w wyniku z głębokością 0 — to potrzebne,
    żeby kinship() poprawnie sumował po „samym sobie" (gdyby ktoś próbował
    skrzyżować zwierzę z jego przodkiem — F będzie wysokie i alarmujące).
    """
    # Import lokalny, żeby uniknąć cyklu na poziomie importów modułów.
    from ..models.animal import Animal

    seen: dict[int, int] = {animal_id: 0}
    queue: deque[tuple[int, int]] = deque([(animal_id, 0)])

    while queue:
        current_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        animal = Animal.query.get(current_id)
        if animal is None:
            continue
        for parent_id in (animal.sire_id, animal.dam_id):
            if parent_id is None or parent_id in seen:
                continue
            seen[parent_id] = depth + 1
            queue.append((parent_id, depth + 1))

    return seen


def inbreeding_coefficient(animal_x: Animal, animal_y: Animal, max_depth: int = 4) -> float:
    """Oczekiwany współczynnik inbredu potomstwa pary (X, Y).

    Zwraca wartość 0.0-1.0. Próg ostrzegawczy w hodowli psów/koni: 0.0625
    (ekwiwalent skrzyżowania kuzynów); poniżej 0.03 uznajemy za „bezpieczne".
    """
    if animal_x.id == animal_y.id:
        return 1.0  # to samo zwierzę

    a_ancestors = collect_ancestors(animal_x.id, max_depth)
    b_ancestors = collect_ancestors(animal_y.id, max_depth)

    common_ids = set(a_ancestors) & set(b_ancestors)

    f = 0.0
    for ancestor_id in common_ids:
        n1 = a_ancestors[ancestor_id]
        n2 = b_ancestors[ancestor_id]
        # Pomijamy przypadek, kiedy X lub Y są przodkami siebie nawzajem na ścieżce
        # — to obsługujemy wcześniej (parent w drzewie drugiego). 1+F_A=1 (brak danych).
        f += 0.5 ** (n1 + n2 + 1)

    return min(f, 1.0)


def risk_label(f: float) -> tuple[str, str]:
    """Zwraca (etykieta, kolor) dla wartości inbredu — do UI."""
    if f < 0.03:
        return ("Niski", "success")
    if f < 0.0625:
        return ("Umiarkowany", "warning")
    if f < 0.125:
        return ("Wysoki", "danger")
    return ("Bardzo wysoki", "danger")
