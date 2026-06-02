"""Fabryka aplikacji Flask.

Wzorzec create_app() oddziela budowę aplikacji od globalnego stanu — łatwiej
testować (każdy test może dostać świeżą instancję) i łatwiej hostować
(gunicorn na produkcji robi `wsgi:app`, dev robi `python wsgi.py`).
"""

from __future__ import annotations

import os

from flask import Flask, render_template

from .extensions import csrf, db, limiter, login_manager, migrate, socketio

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
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Zaloguj się, aby kontynuować."
    login_manager.login_message_category = "warning"
    csrf.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)

    # Modele muszą się zaimportować zanim Alembic spróbuje wykryć schemat.
    from . import models  # noqa: F401

    # User loader Flask-Login — bez tego context_processor wywala wyjątek.
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Rejestracja blueprintów.
    from .routes.animals import bp as animals_bp
    from .routes.api import bp as api_bp
    from .routes.auth import bp as auth_bp
    from .routes.chat import bp as chat_bp
    from .routes.farms import bp as farms_bp
    from .routes.main import bp as main_bp
    from .routes.map import bp as map_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(farms_bp, url_prefix="/farms")
    app.register_blueprint(animals_bp, url_prefix="/animals")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(map_bp, url_prefix="/map")
    app.register_blueprint(api_bp, url_prefix="/api")

    # API operuje na JSON-ie z naszego frontu; cookie sesji ma SameSite=Lax,
    # co odcina klasyczny CSRF z innych domen (Lab 9). Endpointy modyfikujące
    # i tak wymagają zalogowanego użytkownika.
    csrf.exempt(api_bp)

    # Handlery Socket.IO — rejestracja przez import (side effect).
    from flask_login import current_user

    # Context processor: nieprzeczytane powiadomienia widoczne w nawigacji.
    from .models.notification import Notification
    from .sockets import chat as _chat_sockets  # noqa: F401
    from .sockets import notifications as _notif_sockets  # noqa: F401

    @app.context_processor
    def inject_globals():
        unread = 0
        if current_user.is_authenticated:
            unread = (
                db.session.query(Notification)
                .filter_by(recipient_id=current_user.id, is_read=False)
                .count()
            )
        return {"unread_notifications": unread}

    # Strony błędów — używamy własnych, eleganckich.
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "errors/error.html",
            code=403,
            title="Brak dostępu",
            message="Nie masz uprawnień do tego zasobu.",
        ), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "errors/error.html",
            code=404,
            title="Nie znaleziono",
            message="Strona, której szukasz, nie istnieje.",
        ), 404

    @app.errorhandler(429)
    def too_many(_e):
        return render_template(
            "errors/error.html",
            code=429,
            title="Zbyt wiele prób",
            message="Spróbuj ponownie za chwilę.",
        ), 429

    # CLI: seed danych testowych.
    from .seeds import register_cli

    register_cli(app)

    return app


def _configure(app: Flask) -> None:
    default_db_uri = f"sqlite:///{os.path.join(_INSTANCE_DIR, 'tindog.db')}"
    db_uri = _normalize_sqlite_uri(os.environ.get("DATABASE_URL", default_db_uri))

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Cookie sesji — Lab 9. SECURE włączymy świadomie w produkcji (HTTPS).
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Limit rozmiaru żądania (16 MB) — Lab 9, ochrona przed DoS via duże uploady.
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        WTF_CSRF_TIME_LIMIT=3600,
    )


def _normalize_sqlite_uri(uri: str) -> str:
    """Dla SQLite zamienia ścieżkę względną na absolutną względem repo
    i upewnia się, że katalog rodzica istnieje.

    Bez tego `sqlite:///instance/tindog.db` w `.env` ląduje jako ścieżka
    względna do bieżącego katalogu wywołania (np. `flask db migrate` z innego
    miejsca) i SQLite zwraca „unable to open database file".
    """
    prefix_rel = "sqlite:///"
    prefix_abs = "sqlite:////"
    if not uri.startswith(prefix_rel) or uri.startswith(prefix_abs):
        return uri
    rel_path = uri[len(prefix_rel) :]
    abs_path = os.path.normpath(os.path.join(_REPO_ROOT, rel_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    return f"sqlite:///{abs_path}"
