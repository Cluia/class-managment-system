"""Testes de comportamentos de segurança."""

import pytest

from app.config import Config
from app.security import public_error_message


def test_public_error_hides_detail_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    payload = public_error_message("segredo interno")
    assert "detail" not in payload


def test_public_error_shows_detail_in_development(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    payload = public_error_message("detalhe dev")
    assert payload.get("detail") == "detalhe dev"


def test_production_rejects_weak_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")
    with pytest.raises(RuntimeError):
        Config.validate_production()
