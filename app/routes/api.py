"""JSON REST API.

Każdy endpoint:
1. waliduje wejście Pydantic-iem przed dotknięciem bazy (Lab 6, Lab 9),
2. używa wyłącznie ORM SQLAlchemy (Lab 9 — zero raw SQL),
3. sprawdza autoryzację właściciela przed modyfikacją (Lab 9).
"""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError

from ..extensions import db
from ..models.animal import Animal
from ..models.farm import Farm
from ..schemas.animal import AnimalCreate, AnimalRead, AnimalUpdate
from ..schemas.farm import FarmCreate, FarmRead, FarmUpdate
from ..services.matching import find_matches
from ..services.pedigree import collect_ancestors, inbreeding_coefficient

bp = Blueprint("api", __name__)


def _validation_error(exc: ValidationError):
    return jsonify({"error": "validation_error", "details": exc.errors()}), 400


@bp.get("/farms")
def api_list_farms():
    species = request.args.get("species")
    query = Farm.query
    if species in {"dog", "horse", "cat"}:
        query = query.filter(Farm.species == species)
    farms = query.order_by(Farm.name).all()
    return jsonify([FarmRead.model_validate(f).model_dump() for f in farms])


@bp.get("/farms/<int:farm_id>")
def api_farm_detail(farm_id: int):
    farm = db.session.get(Farm, farm_id)
    if farm is None:
        abort(404)
    return jsonify(FarmRead.model_validate(farm).model_dump())


@bp.post("/farms")
@login_required
def api_create_farm():
    try:
        data = FarmCreate.model_validate_json(request.get_data(as_text=True))
    except ValidationError as exc:
        return _validation_error(exc)
    farm = Farm(owner_id=current_user.id, **data.model_dump(exclude_none=False, mode="json"))
    db.session.add(farm)
    db.session.commit()
    return jsonify(FarmRead.model_validate(farm).model_dump()), 201


@bp.patch("/farms/<int:farm_id>")
@login_required
def api_update_farm(farm_id: int):
    farm = db.session.get(Farm, farm_id)
    if farm is None:
        abort(404)
    if farm.owner_id != current_user.id:
        abort(403)
    try:
        data = FarmUpdate.model_validate_json(request.get_data(as_text=True))
    except ValidationError as exc:
        return _validation_error(exc)
    for key, value in data.model_dump(exclude_none=False, mode="json").items():
        setattr(farm, key, value)
    db.session.commit()
    return jsonify(FarmRead.model_validate(farm).model_dump())


@bp.get("/animals")
def api_list_animals():
    species = request.args.get("species")
    sex = request.args.get("sex")
    available = request.args.get("available")
    query = Animal.query
    if species in {"dog", "horse", "cat"}:
        query = query.filter(Animal.species == species)
    if sex in {"male", "female"}:
        query = query.filter(Animal.sex == sex)
    if available == "1":
        query = query.filter(Animal.available_for_breeding.is_(True))
    animals = query.order_by(Animal.created_at.desc()).limit(100).all()
    return jsonify([AnimalRead.model_validate(a).model_dump() for a in animals])


@bp.get("/animals/<int:animal_id>")
def api_animal_detail(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    return jsonify(AnimalRead.model_validate(animal).model_dump())


@bp.get("/animals/<int:animal_id>/pedigree")
def api_animal_pedigree(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    ancestors = collect_ancestors(animal_id, max_depth=4)
    payload = []
    for ancestor_id, generation in ancestors.items():
        a = db.session.get(Animal, ancestor_id)
        if a is None:
            continue
        payload.append(
            {
                "id": a.id,
                "name": a.name,
                "sex": a.sex,
                "breed": a.breed,
                "generation": generation,
                "sire_id": a.sire_id,
                "dam_id": a.dam_id,
            }
        )
    return jsonify({"animal_id": animal_id, "ancestors": payload})


@bp.get("/animals/<int:animal_id>/matches")
def api_animal_matches(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    suggestions = find_matches(animal)
    return jsonify(
        [
            {
                "animal": AnimalRead.model_validate(s.candidate).model_dump(),
                "inbreeding_coefficient": round(s.inbreeding, 5),
                "distance_km": round(s.distance_km, 1) if s.distance_km is not None else None,
            }
            for s in suggestions
        ]
    )


@bp.post("/animals")
@login_required
def api_create_animal():
    if current_user.main_farm is None:
        abort(409, description="Najpierw utwórz hodowlę.")
    try:
        data = AnimalCreate.model_validate_json(request.get_data(as_text=True))
    except ValidationError as exc:
        return _validation_error(exc)
    payload = data.model_dump(mode="json")
    animal = Animal(farm_id=current_user.main_farm.id, **payload)
    db.session.add(animal)
    db.session.commit()
    return jsonify(AnimalRead.model_validate(animal).model_dump()), 201


@bp.patch("/animals/<int:animal_id>")
@login_required
def api_update_animal(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    if animal.farm.owner_id != current_user.id:
        abort(403)
    try:
        data = AnimalUpdate.model_validate_json(request.get_data(as_text=True))
    except ValidationError as exc:
        return _validation_error(exc)
    for key, value in data.model_dump(mode="json").items():
        setattr(animal, key, value)
    db.session.commit()
    return jsonify(AnimalRead.model_validate(animal).model_dump())


@bp.get("/inbreeding")
def api_inbreeding():
    """Liczy oczekiwany inbred potomstwa dwóch zwierząt.

    Przykład: /api/inbreeding?a=1&b=2
    """
    a_id = request.args.get("a", type=int)
    b_id = request.args.get("b", type=int)
    if not a_id or not b_id:
        abort(400, description="Wymagane parametry 'a' i 'b'.")
    a = db.session.get(Animal, a_id)
    b = db.session.get(Animal, b_id)
    if a is None or b is None:
        abort(404)
    f = inbreeding_coefficient(a, b)
    return jsonify(
        {
            "animal_a": a_id,
            "animal_b": b_id,
            "inbreeding_coefficient": round(f, 5),
            "expected_offspring_inbreeding_percent": round(f * 100, 2),
        }
    )


@bp.get("/docs")
def api_docs():
    """Mini-dokumentacja API — do czasu wdrożenia Swaggera z Lab 6."""
    endpoints = [
        ("GET", "/api/farms", "Lista hodowli (opcjonalny filtr ?species=)"),
        ("GET", "/api/farms/<id>", "Profil hodowli"),
        ("POST", "/api/farms", "Utwórz hodowlę (wymaga zalogowania, walidacja Pydantic)"),
        ("PATCH", "/api/farms/<id>", "Edycja hodowli (właściciel)"),
        ("GET", "/api/animals", "Lista zwierząt (?species=&sex=&available=1)"),
        ("GET", "/api/animals/<id>", "Profil zwierzęcia"),
        ("GET", "/api/animals/<id>/pedigree", "Drzewo przodków do 4 pokoleń"),
        ("GET", "/api/animals/<id>/matches", "Sugerowane dopasowania (z inbredem i odległością)"),
        ("POST", "/api/animals", "Dodaj zwierzę do swojej hodowli"),
        ("PATCH", "/api/animals/<id>", "Edycja zwierzęcia (właściciel)"),
        ("GET", "/api/inbreeding?a=X&b=Y", "Współczynnik inbredu potomstwa pary"),
    ]
    return jsonify(
        {"endpoints": [{"method": m, "path": p, "description": d} for m, p, d in endpoints]}
    )
