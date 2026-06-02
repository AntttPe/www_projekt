"""Czat: lista konwersacji, wątek 1:1, rozpoczęcie konwersacji.

Realne wiadomości lecą przez Socket.IO (app/sockets/chat.py). REST tylko
do otwarcia widoku i utworzenia konwersacji.
"""

from __future__ import annotations

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..models.conversation import Conversation
from ..models.user import User

bp = Blueprint("chat", __name__)


def _get_or_create_conversation(user_a_id: int, user_b_id: int) -> Conversation:
    """Zwraca istniejącą rozmowę między dwoma użytkownikami lub tworzy nową.

    Para jest nieuporządkowana — szukamy w obu kierunkach.
    """
    if user_a_id == user_b_id:
        abort(400)
    conv = Conversation.query.filter(
        or_(
            db.and_(Conversation.user_a_id == user_a_id, Conversation.user_b_id == user_b_id),
            db.and_(Conversation.user_a_id == user_b_id, Conversation.user_b_id == user_a_id),
        )
    ).first()
    if conv is None:
        conv = Conversation(user_a_id=user_a_id, user_b_id=user_b_id)
        db.session.add(conv)
        db.session.commit()
    return conv


@bp.get("/")
@login_required
def chat_index():
    conversations = (
        Conversation.query.filter(
            or_(
                Conversation.user_a_id == current_user.id,
                Conversation.user_b_id == current_user.id,
            )
        )
        .order_by(Conversation.created_at.desc())
        .all()
    )
    active_id = request.args.get("conversation_id", type=int)
    active = None
    messages = []
    if active_id:
        active = db.session.get(Conversation, active_id)
        if active and current_user.id not in (active.user_a_id, active.user_b_id):
            abort(403)
        if active:
            messages = active.messages
    return render_template(
        "chat/index.html",
        conversations=conversations,
        active=active,
        messages=messages,
    )


@bp.post("/start/<int:user_id>")
@login_required
def start_with_user(user_id: int):
    other = db.session.get(User, user_id)
    if other is None:
        abort(404)
    conv = _get_or_create_conversation(current_user.id, user_id)
    return redirect(url_for("chat.chat_index", conversation_id=conv.id))
