"""Tymczasowy ping/pong do weryfikacji transportu Socket.IO przez proxy AGH.

Po podłączeniu modeli wiadomości i pokoi rozszerzymy ten plik o realny czat.
"""

from flask import current_app
from flask_socketio import emit

from .. import socketio


@socketio.on("connect")
def handle_connect():
    current_app.logger.info("Socket.IO: nowe połączenie")


@socketio.on("ping_test")
def handle_ping(data):
    # Echo z powrotem do nadawcy — pozwala frontowi potwierdzić dwukierunkowy kanał.
    emit("pong_test", {"received": data})
