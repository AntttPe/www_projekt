"""Strony główne (homepage, status). Pełna mapa stron pojawi się wraz z modelami."""

from flask import Blueprint, render_template
from sqlalchemy import text

from .. import db

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    # Sprawdzamy, czy SQLite odpowiada. Wynik trafia na stronę statusu jako trzecia dioda.
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return render_template("index.html", db_ok=db_ok)
