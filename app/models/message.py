"""Pojedyncza wiadomość w konwersacji."""

from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True
    )
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")
