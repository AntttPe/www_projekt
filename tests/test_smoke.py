"""Smoke test — minimalna weryfikacja, że aplikacja startuje i strona główna odpowiada 200.

Test używa świeżej bazy SQLite w pamięci, żeby NIE wymagał wcześniejszej
migracji ani `flask seed`.
"""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    application.config["WTF_CSRF_ENABLED"] = False
    with application.app_context():
        db.create_all()
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hodowla" in response.data


def test_farms_list_returns_200(client):
    response = client.get("/farms/")
    assert response.status_code == 200


def test_animals_list_returns_200(client):
    response = client.get("/animals/")
    assert response.status_code == 200


def test_api_farms_returns_json(client):
    response = client.get("/api/farms")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


def test_login_page_renders(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Zaloguj" in response.data
