"""Powiadomienia in-app, opcjonalnie wypychane przez Socket.IO w czasie rzeczywistym."""

from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(60), nullable=False)
    # JSON z dodatkowym kontekstem (np. nadawca, id wiadomości, link).
    payload = db.Column(db.JSON, nullable=False, default=dict)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    recipient = db.relationship("User", back_populates="notifications")
