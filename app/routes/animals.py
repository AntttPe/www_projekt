"""Zwierzęta: lista, profil z rodowodem, edycja, dopasowania."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

from ..extensions import db
from ..models.animal import SEX_CHOICES, Animal
from ..models.farm import SPECIES_CHOICES
from ..models.favorite import Favorite
from ..services.matching import find_matches
from ..services.pedigree import inbreeding_coefficient, risk_label

bp = Blueprint("animals", __name__)


class AnimalForm(FlaskForm):
    name = StringField("Imię", validators=[DataRequired(), Length(min=1, max=120)])
    species = SelectField("Gatunek", choices=SPECIES_CHOICES, validators=[DataRequired()])
    breed = StringField("Rasa", validators=[DataRequired(), Length(min=2, max=120)])
    sex = SelectField("Płeć", choices=SEX_CHOICES, validators=[DataRequired()])
    birth_date = DateField("Data urodzenia", validators=[Optional()])
    color = StringField("Maść / umaszczenie", validators=[Length(max=80)])
    registration_number = StringField("Numer rodowodowy", validators=[Length(max=60)])
    title = StringField("Tytuły / osiągnięcia", validators=[Length(max=120)])
    description = TextAreaField("Opis", validators=[Length(max=4000)])
    available_for_breeding = BooleanField("Dostępny/a do rozrodu")
    sire_id = SelectField("Ojciec (z bazy)", coerce=int, choices=[], validators=[Optional()])
    dam_id = SelectField("Matka (z bazy)", coerce=int, choices=[], validators=[Optional()])
    submit = SubmitField("Zapisz")


def _populate_parent_choices(form: AnimalForm, species: str, exclude_id: int | None = None):
    # Tylko zwierzęta tego samego gatunku, posortowane po imieniu.
    q = Animal.query.filter(Animal.species == species)
    if exclude_id is not None:
        q = q.filter(Animal.id != exclude_id)
    males = q.filter(Animal.sex == "male").order_by(Animal.name).all()
    females = q.filter(Animal.sex == "female").order_by(Animal.name).all()
    form.sire_id.choices = [(0, "— nieznany —")] + [(a.id, f"{a.name} ({a.breed})") for a in males]
    form.dam_id.choices = [(0, "— nieznana —")] + [(a.id, f"{a.name} ({a.breed})") for a in females]


@bp.get("/")
def list_animals():
    page = request.args.get("page", 1, type=int)
    species = request.args.get("species", "")
    sex = request.args.get("sex", "")
    available = request.args.get("available") == "1"
    breed = request.args.get("breed", "").strip()
    q = request.args.get("q", "").strip()

    query = Animal.query
    if species in {"dog", "horse", "cat"}:
        query = query.filter(Animal.species == species)
    if sex in {"male", "female"}:
        query = query.filter(Animal.sex == sex)
    if available:
        query = query.filter(Animal.available_for_breeding.is_(True))
    if breed:
        query = query.filter(Animal.breed.ilike(f"%{breed}%"))
    if q:
        like = f"%{q}%"
        query = query.filter((Animal.name.ilike(like)) | (Animal.registration_number.ilike(like)))

    pagination = query.order_by(Animal.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    return render_template(
        "animals/list.html",
        pagination=pagination,
        species_choices=SPECIES_CHOICES,
        sex_choices=SEX_CHOICES,
        filters={
            "species": species,
            "sex": sex,
            "available": "1" if available else "",
            "breed": breed,
            "q": q,
        },
    )


@bp.get("/<int:animal_id>")
def animal_profile(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    is_owner = current_user.is_authenticated and animal.farm.owner_id == current_user.id
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = (
            db.session.query(Favorite)
            .filter_by(user_id=current_user.id, animal_id=animal.id)
            .first()
            is not None
        )

    # Inbred „własny" — jeśli rodzice są ze sobą spokrewnieni, dziecko jest inbredowane.
    own_f = None
    if animal.sire and animal.dam:
        own_f = inbreeding_coefficient(animal.sire, animal.dam)

    return render_template(
        "animals/profile.html",
        animal=animal,
        is_owner=is_owner,
        is_favorited=is_favorited,
        own_inbreeding=own_f,
        risk_label=risk_label,
    )


@bp.get("/<int:animal_id>/matches")
def animal_matches(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    suggestions = find_matches(animal)
    return render_template(
        "animals/matches.html",
        animal=animal,
        suggestions=suggestions,
        risk_label=risk_label,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_animal():
    farm = current_user.main_farm
    if farm is None:
        flash("Najpierw utwórz profil hodowli.", "warning")
        return redirect(url_for("farms.edit_my_farm"))

    form = AnimalForm()
    # Domyślny gatunek = gatunek hodowli; zwykle będzie ten sam.
    if request.method == "GET":
        form.species.data = farm.species
    _populate_parent_choices(form, species=form.species.data or farm.species)

    if form.validate_on_submit():
        animal = Animal(farm_id=farm.id)
        _apply_form(animal, form)
        db.session.add(animal)
        db.session.commit()
        flash(f"Dodano: {animal.name}.", "success")
        return redirect(url_for("animals.animal_profile", animal_id=animal.id))

    return render_template("animals/form.html", form=form, animal=None, farm=farm)


@bp.route("/<int:animal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_animal(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    # Lab 9 — autoryzacja właściciela; zarówno w UI jak i w handlerze.
    if animal.farm.owner_id != current_user.id:
        abort(403)

    form = AnimalForm(obj=animal)
    # Pola enum wymagają jawnego ustawienia (WTForms obj=... potrafi pominąć).
    if request.method == "GET":
        form.species.data = animal.species
        form.sex.data = animal.sex
        form.sire_id.data = animal.sire_id or 0
        form.dam_id.data = animal.dam_id or 0
    _populate_parent_choices(form, species=form.species.data, exclude_id=animal.id)

    if form.validate_on_submit():
        _apply_form(animal, form)
        db.session.commit()
        flash("Zmiany zapisane.", "success")
        return redirect(url_for("animals.animal_profile", animal_id=animal.id))

    return render_template("animals/form.html", form=form, animal=animal, farm=animal.farm)


@bp.post("/<int:animal_id>/delete")
@login_required
def delete_animal(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    if animal.farm.owner_id != current_user.id:
        abort(403)
    farm_id = animal.farm_id
    db.session.delete(animal)
    db.session.commit()
    flash("Usunięto zwierzę.", "success")
    return redirect(url_for("farms.farm_profile", farm_id=farm_id))


@bp.post("/<int:animal_id>/favorite")
@login_required
def toggle_favorite(animal_id: int):
    animal = db.session.get(Animal, animal_id)
    if animal is None:
        abort(404)
    existing = Favorite.query.filter_by(user_id=current_user.id, animal_id=animal_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    else:
        db.session.add(Favorite(user_id=current_user.id, animal_id=animal_id))
        db.session.commit()
    return redirect(request.referrer or url_for("animals.animal_profile", animal_id=animal_id))


def _apply_form(animal: Animal, form: AnimalForm) -> None:
    animal.name = form.name.data.strip()
    animal.species = form.species.data
    animal.breed = form.breed.data.strip()
    animal.sex = form.sex.data
    animal.birth_date = form.birth_date.data
    animal.color = (form.color.data or "").strip()
    animal.registration_number = (form.registration_number.data or "").strip()
    animal.title = (form.title.data or "").strip()
    animal.description = form.description.data or ""
    animal.available_for_breeding = bool(form.available_for_breeding.data)
    animal.sire_id = form.sire_id.data if form.sire_id.data else None
    animal.dam_id = form.dam_id.data if form.dam_id.data else None
