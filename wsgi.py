"""Punkt wejścia aplikacji.

Produkcja (AGH lab):
    gunicorn -k gevent -w 1 --bind unix:$HOME/app.sock wsgi:app

Development lokalnie:
    python wsgi.py
"""

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # socketio.run zamiast `flask run` — werkzeug nie obsługuje WebSocketów poprawnie.
    # Port 5001 zamiast 5000, bo macOS od Monterey trzyma 5000 dla AirPlay Receiver.
    # allow_unsafe_werkzeug=True jest potrzebne dla nowszego Flask-SocketIO w devie.
    socketio.run(app, host="127.0.0.1", port=5001, debug=True, allow_unsafe_werkzeug=True)
