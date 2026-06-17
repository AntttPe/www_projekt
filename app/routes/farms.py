"""Hodowle: lista, profil, edycja własnej, ulubione."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    FloatField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, DataRequired, Email, Length, NumberRange, Optional

from ..extensions import db
from ..models.farm import SPECIES_CHOICES, Farm
from ..models.favorite import Favorite
from ..services.uploads import KIND_PHOTOS, UploadError, delete_upload, save_upload

bp = Blueprint("farms", __name__)


VOIVODESHIPS = [
    "",
    "dolnośląskie",
    "kujawsko-pomorskie",
    "lubelskie",
    "lubuskie",
    "łódzkie",
    "małopolskie",
    "mazowieckie",
    "opolskie",
    "podkarpackie",
    "podlaskie",
    "pomorskie",
    "śląskie",
    "świętokrzyskie",
    "warmińsko-mazurskie",
    "wielkopolskie",
    "zachodniopomorskie",
]


class FarmForm(FlaskForm):
    name = StringField("Nazwa hodowli", validators=[DataRequired(), Length(min=2, max=120)])
    species = SelectField(
        "Gatunek",
        choices=SPECIES_CHOICES,
        validators=[DataRequired()],
    )
    description = TextAreaField("Opis hodowli", validators=[Length(max=4000)])
    city = StringField("Miasto", validators=[Length(max=120)])
    voivodeship = SelectField(
        "Województwo",
        choices=[(v, v.capitalize() if v else "— wybierz —") for v in VOIVODESHIPS],
        validators=[Optional()],
    )
    latitude = FloatField(
        "Szerokość geograficzna",
        validators=[Optional(), NumberRange(min=-90, max=90)],
    )
    longitude = FloatField(
        "Długość geograficzna",
        validators=[Optional(), NumberRange(min=-180, max=180)],
    )
    contact_email = StringField(
        "Email kontaktowy", validators=[Optional(), Email(), Length(max=255)]
    )
    contact_phone = StringField("Telefon", validators=[Length(max=40)])
    website = StringField("Strona WWW", validators=[Optional(), URL(), Length(max=255)])
    # Pierwsza linia obrony (rozszerzenie); druga to sniffing MIME w services/uploads.
    photo = FileField(
        "Zdjęcie hodowli",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Dozwolone: JPG, PNG, WebP.")],
    )
    submit = SubmitField("Zapisz")


@bp.get("/")
def list_farms():
    page = request.args.get("page", 1, type=int)
    species = request.args.get("species", "")
    voivodeship = request.args.get("voivodeship", "")
    verified_only = request.args.get("verified") == "1"
    q = request.args.get("q", "").strip()

    query = Farm.query
    if species in {"dog", "horse", "cat"}:
        query = query.filter(Farm.species == species)
    if voivodeship:
        query = query.filter(Farm.voivodeship == voivodeship)
    if verified_only:
        query = query.filter(Farm.is_verified.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter((Farm.name.ilike(like)) | (Farm.city.ilike(like)))

    pagination = query.order_by(Farm.is_verified.desc(), Farm.name.asc()).paginate(
        page=page, per_page=9, error_out=False
    )

    favorited_farm_ids = set()
    if current_user.is_authenticated:
        favorited_farm_ids = {
            f.farm_id
            for f in Favorite.query.filter_by(user_id=current_user.id)
            .filter(Favorite.farm_id.is_not(None))
            .all()
        }

    # Wartości w filtrach trzymamy jako stringi, żeby `**filters` w url_for
    # round-trip-owało poprawnie (`True` → `1`).
    return render_template(
        "farms/list.html",
        pagination=pagination,
        species_choices=SPECIES_CHOICES,
        voivodeships=VOIVODESHIPS,
        filters={
            "species": species,
            "voivodeship": voivodeship,
            "verified": "1" if verified_only else "",
            "q": q,
        },
        favorited_farm_ids=favorited_farm_ids,
    )


@bp.get("/me")
@login_required
def my_farm():
    farm = current_user.main_farm
    if farm is None:
        return redirect(url_for("farms.edit_my_farm"))
    return redirect(url_for("farms.farm_profile", farm_id=farm.id))


@bp.route("/me/edit", methods=["GET", "POST"])
@login_required
def edit_my_farm():
    farm = current_user.main_farm
    form = FarmForm(obj=farm)

    if form.validate_on_submit():
        # Walidujemy/zapisujemy plik ZANIM dotkniemy bazy — przy błędzie nic nie commitujemy.
        try:
            new_photo = save_upload(form.photo.data, kind=KIND_PHOTOS)
        except UploadError as exc:
            flash(str(exc), "danger")
            return render_template("farms/edit.html", form=form, farm=farm)

        is_new = farm is None
        if is_new:
            farm = Farm(owner_id=current_user.id)
            db.session.add(farm)
        # Ręczne kopiowanie, żeby NIE pozwolić użytkownikowi przepisać is_verified/owner_id.
        farm.name = form.name.data
        farm.species = form.species.data
        farm.description = form.description.data or ""
        farm.city = form.city.data or ""
        farm.voivodeship = form.voivodeship.data or ""
        farm.latitude = form.latitude.data
        farm.longitude = form.longitude.data
        farm.contact_email = form.contact_email.data or ""
        farm.contact_phone = form.contact_phone.data or ""
        farm.website = form.website.data or ""
        if new_photo:
            delete_upload(farm.photo_filename, kind=KIND_PHOTOS)  # sprzątamy stare zdjęcie
            farm.photo_filename = new_photo
        db.session.commit()
        flash("Profil hodowli zapisany.", "success")
        return redirect(url_for("farms.farm_profile", farm_id=farm.id))

    return render_template("farms/edit.html", form=form, farm=farm)


@bp.get("/<int:farm_id>")
def farm_profile(farm_id: int):
    farm = db.session.get(Farm, farm_id)
    if farm is None:
        abort(404)
    is_owner = current_user.is_authenticated and farm.owner_id == current_user.id
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = (
            db.session.query(Favorite).filter_by(user_id=current_user.id, farm_id=farm.id).first()
            is not None
        )
    return render_template(
        "farms/profile.html", farm=farm, is_owner=is_owner, is_favorited=is_favorited
    )


@bp.post("/<int:farm_id>/favorite")
@login_required
def toggle_favorite(farm_id: int):
    farm = db.session.get(Farm, farm_id)
    if farm is None:
        abort(404)
    existing = Favorite.query.filter_by(user_id=current_user.id, farm_id=farm_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Usunięto z ulubionych.", "success")
    else:
        db.session.add(Favorite(user_id=current_user.id, farm_id=farm_id))
        db.session.commit()
        flash("Dodano do ulubionych.", "success")
    return redirect(request.referrer or url_for("farms.farm_profile", farm_id=farm_id))
