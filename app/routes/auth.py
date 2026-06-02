"""Rejestracja, logowanie, wylogowanie.

Hasła hashowane argon2 w modelu User (Lab 9). Rate limiting na rejestracji
i logowaniu chroni przed botami i brute-force. CSRF token w formularzach
domyślnie przez Flask-WTF.
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from ..extensions import db, limiter
from ..models.user import User

bp = Blueprint("auth", __name__)


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    display_name = StringField("Nazwa hodowcy", validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField("Hasło", validators=[DataRequired(), Length(min=8, max=200)])
    password_confirm = PasswordField(
        "Powtórz hasło",
        validators=[DataRequired(), EqualTo("password", message="Hasła muszą być takie same.")],
    )
    submit = SubmitField("Załóż konto")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    submit = SubmitField("Zaloguj się")


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Konto z tym adresem już istnieje.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(email=email, display_name=form.display_name.data.strip())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Witaj w społeczności, {user.display_name}!", "success")
        # Po rejestracji prowadzimy od razu do utworzenia hodowli.
        return redirect(url_for("farms.edit_my_farm"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f"Witaj ponownie, {user.display_name}.", "success")
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
        # Komunikat ogólnikowy, żeby nie zdradzać czy konto istnieje (Lab 9).
        flash("Nieprawidłowy email lub hasło.", "danger")

    return render_template("auth/login.html", form=form)


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Wylogowano.", "success")
    return redirect(url_for("main.index"))
