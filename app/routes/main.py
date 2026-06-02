"""Strony główne: landing, dashboard, powiadomienia."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models.animal import Animal
from ..models.farm import Farm
from ..models.notification import Notification

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    featured = Farm.query.order_by(Farm.is_verified.desc(), Farm.created_at.desc()).limit(6).all()
    stats = {
        "farms": db.session.scalar(db.select(func.count(Farm.id))) or 0,
        "animals": db.session.scalar(db.select(func.count(Animal.id))) or 0,
        "verified": db.session.scalar(
            db.select(func.count(Farm.id)).where(Farm.is_verified.is_(True))
        )
        or 0,
    }
    return render_template("index.html", featured=featured, stats=stats)


@bp.get("/dashboard")
@login_required
def dashboard():
    farm = current_user.main_farm
    recent_notifications = (
        Notification.query.filter_by(recipient_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template("dashboard.html", farm=farm, recent_notifications=recent_notifications)


@bp.get("/notifications")
@login_required
def notifications():
    items = (
        Notification.query.filter_by(recipient_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", items=items)


@bp.post("/notifications/<int:notif_id>/read")
@login_required
def mark_read(notif_id: int):
    notif = db.session.get(Notification, notif_id)
    if notif is None:
        abort(404)
    if notif.recipient_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    return redirect(url_for("main.notifications"))


@bp.post("/notifications/read-all")
@login_required
def mark_all_read():
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update(
        {"is_read": True, "read_at": datetime.utcnow()}
        if hasattr(Notification, "read_at")
        else {"is_read": True}
    )
    db.session.commit()
    return redirect(url_for("main.notifications"))
