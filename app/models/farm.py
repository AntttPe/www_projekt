"""Model hodowli."""

from __future__ import annotations

from datetime import datetime

from ..extensions import db

SPECIES_CHOICES = [
    ("dog", "Psy"),
    ("horse", "Konie"),
    ("cat", "Koty"),
]


class Farm(db.Model):
    __tablename__ = "farms"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    species = db.Column(db.String(20), nullable=False, index=True)  # dog | horse | cat
    city = db.Column(db.String(120), nullable=False, default="")
    voivodeship = db.Column(db.String(60), nullable=False, default="")
    # Współrzędne do mapy i filtrowania po promieniu (Leaflet + haversine).
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    accent_color = db.Column(db.String(20), nullable=False, default="green")
    contact_email = db.Column(db.String(255), nullable=False, default="")
    contact_phone = db.Column(db.String(40), nullable=False, default="")
    website = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    owner = db.relationship("User", back_populates="farms")
    animals = db.relationship("Animal", back_populates="farm", cascade="all, delete-orphan")

    @property
    def species_label(self) -> str:
        return dict(SPECIES_CHOICES).get(self.species, self.species)
