"""Fixtures compartilhadas para testes."""

import pytest

from app import create_test_app


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")


@pytest.fixture
def app():
    application = create_test_app()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_plan_data():
    return {
        "title": "Introdução ao OSPF",
        "objective": "Compreender fundamentos de roteamento dinâmico.",
        "syllabus_summary": "Aula introdutória sobre protocolos OSPF em redes.",
        "scheduled_date": "2026-06-15",
        "subject": "Redes",
        "contents": ["Conceitos", "Configuração básica"],
        "support_resources": ["Slides", "Laboratório"],
        "tags": ["redes", "OSPF"],
    }


@pytest.fixture
def created_plan(client, sample_plan_data):
    response = client.post("/api/plans", json=sample_plan_data)
    assert response.status_code == 201
    return response.get_json()
