"""Fabryka aplikacji Flask.

Wzorzec create_app() oddziela budowę aplikacji od globalnego stanu — łatwiej
testować (każdy test może dostać świeżą instancję) i łatwiej hostować
(gunicorn na produkcji robi `wsgi:app`, dev robi `python wsgi.py`).
"""

from __future__ import annotations

import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Rozszerzenia trzymamy na poziomie modułu, żeby blueprinty/handlery mogły je importować.
# Realne podpięcie do aplikacji dzieje się w create_app() przez .init_app(app).
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# async_mode="gevent" zgodne z workerem gunicorna na AGH lab (Lab 8).
socketio = SocketIO(async_mode="gevent")


# Ścieżki bazowe — instance/ ląduje w katalogu repo, NIE wewnątrz pakietu app/.
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_PACKAGE_DIR)
_INSTANCE_DIR = os.path.join(_REPO_ROOT, "instance")


def create_app() -> Flask:
    os.makedirs(_INSTANCE_DIR, exist_ok=True)

    app = Flask(__name__, instance_path=_INSTANCE_DIR)
    _configure(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Tymczasowy user_loader. Bez niego Flask-Login wywala wyjątek na KAŻDYM
    # renderze szablonu, bo context_processor próbuje załadować current_user.
    # Zostanie podmieniony na realny lookup po dodaniu modelu User (zadanie #9).
    @login_manager.user_loader
    def _load_user(user_id: str):
        return None

    # Rejestracja blueprintów (REST + strony).
    from .routes.main import bp as main_bp

    app.register_blueprint(main_bp)

    # Import handlerów Socket.IO — wykonanie modułu rejestruje eventy w globalnym `socketio`.
    from .sockets import chat  # noqa: F401

    return app


def _configure(app: Flask) -> None:
    default_db_uri = f"sqlite:///{os.path.join(_INSTANCE_DIR, 'tindog.db')}"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", default_db_uri),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Cookie sesji — Lab 9. SECURE włączamy świadomie w produkcji (kiedy HTTPS).
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Limit rozmiaru żądania (16 MB) — Lab 9, ochrona przed DoS przez wielkie uploady.
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )
