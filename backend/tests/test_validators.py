"""Testes de validação Pydantic."""

import pytest
from pydantic import ValidationError

from app.validators import (
    ClassPlanCreateSchema,
    ClassPlanUpdateSchema,
    PlanListQuerySchema,
    RecommendationsSchema,
)


def test_create_schema_rejects_empty_title():
    with pytest.raises(ValidationError):
        ClassPlanCreateSchema.model_validate(
            {
                "title": "   ",
                "objective": "Objetivo válido aqui.",
                "syllabus_summary": "Ementa com conteúdo suficiente.",
                "scheduled_date": "2026-06-15",
                "subject": "Redes",
                "contents": ["A"],
                "support_resources": ["B"],
                "tags": ["c"],
            }
        )


def test_create_schema_accepts_comma_separated_lists():
    data = ClassPlanCreateSchema.model_validate(
        {
            "title": "Aula de Redes",
            "objective": "Aprender OSPF na prática.",
            "syllabus_summary": "Ementa detalhada da disciplina de redes.",
            "scheduled_date": "2026-06-15",
            "subject": "Redes",
            "contents": "Conceitos, Prática",
            "support_resources": "Slides",
            "tags": "redes, OSPF",
        }
    )
    assert data.contents == ["Conceitos", "Prática"]
    assert data.tags == ["redes", "OSPF"]


def test_update_schema_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        ClassPlanUpdateSchema.model_validate({})


def test_recommendations_schema_requires_ementa():
    with pytest.raises(ValidationError):
        RecommendationsSchema.model_validate(
            {
                "title": "Título válido",
                "subject": "Redes",
                "syllabus_summary": "   ",
            }
        )


def test_list_query_pagination_bounds():
    with pytest.raises(ValidationError):
        PlanListQuerySchema.model_validate({"page": 0})

    data = PlanListQuerySchema.model_validate({"per_page": 50})
    assert data.per_page == 50
