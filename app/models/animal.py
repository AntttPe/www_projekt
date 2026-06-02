"""Model zwierzęcia + self-reference dla rodowodu.

`sire_id` (ojciec) i `dam_id` (matka) tworzą graf przodków. Przeglądanie
rodowodu = rekurencyjne schodzenie po tych dwóch polach (patrz
`services/pedigree.py`).
"""

from __future__ import annotations

from datetime import datetime

from ..extensions import db

SEX_CHOICES = [("male", "Samiec"), ("female", "Samica")]


class Animal(db.Model):
    __tablename__ = "animals"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(20), nullable=False, index=True)
    breed = db.Column(db.String(120), nullable=False, index=True)
    sex = db.Column(db.String(10), nullable=False)  # male | female
    birth_date = db.Column(db.Date)
    color = db.Column(db.String(80), nullable=False, default="")
    registration_number = db.Column(db.String(60), nullable=False, default="", index=True)
    description = db.Column(db.Text, nullable=False, default="")
    available_for_breeding = db.Column(db.Boolean, nullable=False, default=False)
    title = db.Column(db.String(120), nullable=False, default="")  # np. "Mistrz Polski"

    sire_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=True, index=True)
    dam_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    farm = db.relationship("Farm", back_populates="animals")
    sire = db.relationship(
        "Animal", foreign_keys=[sire_id], remote_side=[id], lazy="joined", post_update=True
    )
    dam = db.relationship(
        "Animal", foreign_keys=[dam_id], remote_side=[id], lazy="joined", post_update=True
    )

    @property
    def sex_label(self) -> str:
        return dict(SEX_CHOICES).get(self.sex, self.sex)

    @property
    def age_years(self) -> int | None:
        if not self.birth_date:
            return None
        today = datetime.utcnow().date()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years
