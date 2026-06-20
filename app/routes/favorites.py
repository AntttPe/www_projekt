"""Ulubione: widok zbiorczy polubionych zwierząt i hodowli."""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models.animal import Animal
from ..models.farm import Farm
from ..models.favorite import Favorite

bp = Blueprint("favorites", __name__, url_prefix="/favorites")


@bp.get("/")
@login_required
def index():
    # Pobieramy wszystkie polubienia obecnego użytkownika
    favs = Favorite.query.filter_by(user_id=current_user.id).all()

    # Wyciągamy ID polubionych zwierząt i hodowli
    animal_ids = [f.animal_id for f in favs if f.animal_id]
    farm_ids = [f.farm_id for f in favs if f.farm_id]

    # Pobieramy pełne obiekty z bazy
    # In() jest wydajniejsze niż robienie zapytania dla każdego ID osobno
    animals = Animal.query.filter(Animal.id.in_(animal_ids)).all() if animal_ids else []
    farms = Farm.query.filter(Farm.id.in_(farm_ids)).all() if farm_ids else []

    # Przekazujemy listy ID z powrotem, żeby gwiazdki na tych kartach też były zamalowane
    return render_template(
        "favorites/index.html",
        animals=animals,
        farms=farms,
        favorited_animal_ids=set(animal_ids),
        favorited_farm_ids=set(farm_ids),
    )
