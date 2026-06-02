"""Handlery Socket.IO dla czatu w czasie rzeczywistym.

Klient po wejściu do konwersacji emituje `join_conversation` — serwer
weryfikuje uprawnienia i dodaje do pokoju o id konwersacji. Wiadomości
emitowane do tego pokoju trafiają do obu rozmówców.
"""

from __future__ import annotations

from datetime import datetime

from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from ..extensions import db, socketio
from ..models.conversation import Conversation
from ..models.message import Message
from ..models.notification import Notification


def _room(conversation_id: int) -> str:
    return f"conv:{conversation_id}"


def _user_room(user_id: int) -> str:
    return f"user:{user_id}"


@socketio.on("connect")
def handle_connect():
    if current_user.is_authenticated:
        # Pokój osobisty użytkownika — używany do powiadomień.
        join_room(_user_room(current_user.id))
        current_app.logger.info("SocketIO: %s połączony (sid=%s)", current_user.email, request.sid)
    else:
        current_app.logger.info("SocketIO: anonim połączony (sid=%s)", request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    current_app.logger.info("SocketIO: rozłączenie sid=%s", request.sid)


@socketio.on("join_conversation")
def handle_join_conversation(data):
    conv_id = data.get("conversation_id") if isinstance(data, dict) else None
    if not isinstance(conv_id, int) or not current_user.is_authenticated:
        emit("error", {"message": "Nieautoryzowany dostęp"})
        return
    conv = db.session.get(Conversation, conv_id)
    if conv is None or current_user.id not in (conv.user_a_id, conv.user_b_id):
        emit("error", {"message": "Brak dostępu do konwersacji"})
        return
    join_room(_room(conv_id))
    emit("joined", {"conversation_id": conv_id})


@socketio.on("leave_conversation")
def handle_leave_conversation(data):
    conv_id = data.get("conversation_id") if isinstance(data, dict) else None
    if isinstance(conv_id, int):
        leave_room(_room(conv_id))


@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        emit("error", {"message": "Zaloguj się, aby pisać."})
        return
    if not isinstance(data, dict):
        emit("error", {"message": "Niepoprawne dane."})
        return

    conv_id = data.get("conversation_id")
    body = (data.get("body") or "").strip()
    # Walidacja po stronie serwera — nie ufamy klientowi (Lab 9).
    if not isinstance(conv_id, int) or not body or len(body) > 2000:
        emit("error", {"message": "Pusta lub za długa wiadomość."})
        return

    conv = db.session.get(Conversation, conv_id)
    if conv is None or current_user.id not in (conv.user_a_id, conv.user_b_id):
        emit("error", {"message": "Brak dostępu."})
        return

    msg = Message(conversation_id=conv_id, sender_id=current_user.id, body=body)
    db.session.add(msg)

    # Powiadomienie dla drugiej osoby.
    other_id = conv.user_b_id if conv.user_a_id == current_user.id else conv.user_a_id
    notif = Notification(
        recipient_id=other_id,
        type="new_message",
        payload={
            "conversation_id": conv_id,
            "from": current_user.display_name,
            "preview": body[:80],
        },
    )
    db.session.add(notif)
    db.session.commit()

    payload = {
        "id": msg.id,
        "conversation_id": conv_id,
        "sender_id": current_user.id,
        "sender_name": current_user.display_name,
        "body": body,
        "sent_at": msg.sent_at.isoformat(timespec="seconds"),
    }
    # Wszyscy w pokoju konwersacji dostają wiadomość.
    socketio.emit("new_message", payload, room=_room(conv_id))
    # Drugi użytkownik dostaje też powiadomienie do swojego osobistego pokoju.
    socketio.emit(
        "notification",
        {
            "type": "new_message",
            "payload": notif.payload,
            "created_at": datetime.utcnow().isoformat(),
        },
        room=_user_room(other_id),
    )
