"""Mapa hodowli (Leaflet + OpenStreetMap)."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from ..extensions import db
from ..models.farm import SPECIES_CHOICES, Farm

bp = Blueprint("map", __name__)


@bp.get("/")
def map_view():
    species = request.args.get("species", "")
    query = db.select(Farm).where(Farm.latitude.is_not(None), Farm.longitude.is_not(None))
    if species in {"dog", "horse", "cat"}:
        query = query.where(Farm.species == species)
    farms = db.session.scalars(query).all()

    farms_payload = [
        {
            "id": f.id,
            "name": f.name,
            "species": f.species,
            "species_label": f.species_label,
            "city": f.city,
            "is_verified": f.is_verified,
            "lat": f.latitude,
            "lng": f.longitude,
            "url": f"/farms/{f.id}",
        }
        for f in farms
    ]
    return render_template(
        "map.html",
        farms_payload=farms_payload,
        species_choices=SPECIES_CHOICES,
        active_species=species,
    )
