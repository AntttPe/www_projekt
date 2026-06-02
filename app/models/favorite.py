"""Ulubione — może wskazywać na zwierzę albo hodowlę (dokładnie jedno z dwóch)."""

from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    animal_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorites")
    animal = db.relationship("Animal")
    farm = db.relationship("Farm")

    __table_args__ = (
        # Wymuszamy, że dokładnie jedno z (animal_id, farm_id) jest ustawione.
        db.CheckConstraint(
            "((animal_id IS NOT NULL) + (farm_id IS NOT NULL)) = 1",
            name="ck_favorite_exactly_one_target",
        ),
        db.UniqueConstraint("user_id", "animal_id", name="uq_favorite_user_animal"),
        db.UniqueConstraint("user_id", "farm_id", name="uq_favorite_user_farm"),
    )
