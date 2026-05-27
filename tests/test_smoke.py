"""Smoke test — minimalna weryfikacja, że aplikacja startuje i strona główna odpowiada 200."""

import pytest

from app import create_app


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hodowla" in response.data
