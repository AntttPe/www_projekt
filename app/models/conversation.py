"""Konwersacja 1:1 między dwoma użytkownikami."""

from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_a_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_a = db.relationship("User", foreign_keys=[user_a_id])
    user_b = db.relationship("User", foreign_keys=[user_b_id])
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sent_at",
    )

    __table_args__ = (db.UniqueConstraint("user_a_id", "user_b_id", name="uq_conversation_pair"),)

    def other_user(self, current_user_id: int):
        """Zwraca rozmówcę, czyli tego użytkownika z pary, który NIE jest current_user."""
        return self.user_b if self.user_a_id == current_user_id else self.user_a
