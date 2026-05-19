"""Endpoints da API — CRUD de planos de aula."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

import httpx

from app import db
from app.security import ai_limit, public_error_message
from app.services import AIResponseError, ClassPlanService
from app.validators import (
    ClassPlanCreateSchema,
    ClassPlanUpdateSchema,
    GeneratePlanSchema,
    PlanListQuerySchema,
    RecommendationsSchema,
    format_validation_errors,
)

api_bp = Blueprint("api", __name__)
plan_service = ClassPlanService()


def _parse_json_body() -> dict:
    if not request.is_json:
        raise BadRequest("Content-Type deve ser application/json.")

    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Corpo da requisição JSON inválido ou vazio.")
    if not isinstance(data, dict):
        raise BadRequest("O corpo da requisição deve ser um objeto JSON.")
    return data


def _validate(schema_class, data: dict):
    try:
        return schema_class.model_validate(data), None
    except ValidationError as exc:
        return None, format_validation_errors(exc)


def _parse_list_query() -> dict:
    raw = request.args.to_dict()
    if "tags" in request.args:
        tag_values = request.args.getlist("tags")
        if len(tag_values) > 1:
            raw["tags"] = tag_values
    return raw


@api_bp.errorhandler(BadRequest)
def handle_bad_request(exc: BadRequest):
    return jsonify({"error": exc.description}), 400


@api_bp.get("/health")
def health():
    from sqlalchemy import text

    payload = {"status": "healthy", "database": "connected"}
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
    return jsonify(payload)


@api_bp.get("/plans")
def list_plans():
    validated, errors = _validate(PlanListQuerySchema, _parse_list_query())
    if errors:
        return jsonify(errors), 400

    result = plan_service.list_plans(validated.model_dump())
    return jsonify(result)


@api_bp.get("/plans/<int:plan_id>")
def get_plan(plan_id: int):
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({"error": "Plano não encontrado."}), 404
    return jsonify(plan.to_dict())


@api_bp.post("/plans")
def create_plan():
    try:
        body = _parse_json_body()
    except BadRequest as exc:
        return jsonify({"error": exc.description}), 400

    validated, errors = _validate(ClassPlanCreateSchema, body)
    if errors:
        return jsonify(errors), 400

    try:
        plan = plan_service.create_plan(validated.model_dump())
    except SQLAlchemyError:
        return jsonify({"error": "Erro ao salvar plano no banco de dados."}), 500

    return jsonify(plan.to_dict()), 201


@api_bp.post("/plans/recommendations")
@ai_limit()
def plan_recommendations():
    try:
        body = _parse_json_body()
    except BadRequest as exc:
        return jsonify({"error": exc.description}), 400

    validated, errors = _validate(RecommendationsSchema, body)
    if errors:
        return jsonify(errors), 400

    try:
        result = plan_service.get_recommendations(validated.model_dump())
    except AIResponseError as exc:
        payload = public_error_message(str(exc))
        payload["error"] = "A IA retornou um formato inválido."
        return jsonify(payload), 502
    except httpx.TimeoutException:
        return (
            jsonify(
                {"error": "Tempo esgotado ao aguardar resposta da IA. Tente novamente."}
            ),
            504,
        )
    except httpx.HTTPError:
        return (
            jsonify(
                {
                    "error": "Não foi possível comunicar com o serviço de IA. Tente novamente."
                }
            ),
            502,
        )

    return jsonify(result)


@api_bp.post("/plans/generate")
@ai_limit()
def generate_plan():
    try:
        body = _parse_json_body()
    except BadRequest as exc:
        return jsonify({"error": exc.description}), 400

    validated, errors = _validate(GeneratePlanSchema, body)
    if errors:
        return jsonify(errors), 400

    try:
        plan = plan_service.generate_and_save(validated.model_dump())
    except ValidationError as exc:
        return jsonify(format_validation_errors(exc)), 400
    except AIResponseError as exc:
        payload = public_error_message(str(exc))
        payload["error"] = "A IA retornou um formato inválido."
        return jsonify(payload), 502
    except httpx.TimeoutException:
        return (
            jsonify(
                {"error": "Tempo esgotado ao aguardar resposta da IA. Tente novamente."}
            ),
            504,
        )
    except httpx.HTTPError:
        return (
            jsonify(
                {
                    "error": "Não foi possível comunicar com o serviço de IA. Tente novamente."
                }
            ),
            502,
        )

    return jsonify(plan.to_dict()), 201


@api_bp.put("/plans/<int:plan_id>")
def update_plan(plan_id: int):
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({"error": "Plano não encontrado."}), 404

    try:
        body = _parse_json_body()
    except BadRequest as exc:
        return jsonify({"error": exc.description}), 400

    validated, errors = _validate(ClassPlanUpdateSchema, body)
    if errors:
        return jsonify(errors), 400

    payload = validated.model_dump(exclude_unset=True)
    try:
        updated = plan_service.update_plan(plan, payload)
    except SQLAlchemyError:
        return jsonify({"error": "Erro ao atualizar plano no banco de dados."}), 500
    return jsonify(updated.to_dict())


@api_bp.patch("/plans/<int:plan_id>")
def patch_plan(plan_id: int):
    return update_plan(plan_id)


@api_bp.delete("/plans/<int:plan_id>")
def delete_plan(plan_id: int):
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return jsonify({"error": "Plano não encontrado."}), 404

    try:
        plan_service.delete_plan(plan)
    except SQLAlchemyError:
        return jsonify({"error": "Erro ao excluir plano no banco de dados."}), 500
    return "", 204
