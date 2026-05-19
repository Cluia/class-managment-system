"""Testes dos modelos e utilitários."""

import pytest

from app.models import parse_str_list


def test_parse_str_list_from_comma_separated():
    assert parse_str_list("a, b, c") == ["a", "b", "c"]


def test_parse_str_list_rejects_invalid_json():
    with pytest.raises(ValueError, match="JSON de lista inválido"):
        parse_str_list("[invalid")
