"""Model użytkownika.

Hasła hashujemy argon2 (Lab 9). Nigdy nie logujemy plaintextu, nigdy nie
zwracamy hash w API.
"""

from __future__ import annotations

from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from flask_login import UserMixin

from ..extensions import db

_ph = PasswordHasher()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user | admin
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    farms = db.relationship("Farm", back_populates="owner", cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship(
        "Notification", back_populates="recipient", cascade="all, delete-orphan"
    )

    def set_password(self, plain: str) -> None:
        self.password_hash = _ph.hash(plain)

    def check_password(self, plain: str) -> bool:
        try:
            _ph.verify(self.password_hash, plain)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def main_farm(self):
        # W obecnym zakresie traktujemy użytkownika jako właściciela jednej hodowli,
        # ale schemat dopuszcza wiele (np. dla rozbudowy w przyszłości).
        return self.farms[0] if self.farms else None
