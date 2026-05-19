"""Camadas de segurança: headers, rate limit e sanitização de erros."""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import Config

limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")


def init_security(app: Flask) -> None:
    _init_cors(app)
    _init_rate_limiter(app)
    _register_headers(app)
    _register_error_handlers(app)


def _init_cors(app: Flask) -> None:
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        supports_credentials=False,
    )


def _init_rate_limiter(app: Flask) -> None:
    app.config.setdefault("RATELIMIT_ENABLED", Config.RATELIMIT_ENABLED)
    limiter.init_app(app)
    limiter.enabled = app.config["RATELIMIT_ENABLED"]


def _register_headers(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        if Config.is_production():
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(413)
    def payload_too_large(_exc):
        return jsonify({"error": "Payload excede o tamanho máximo permitido."}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(_exc):
        return jsonify(
            {"error": "Muitas requisições. Aguarde um momento e tente novamente."}
        ), 429

    @app.errorhandler(500)
    def internal_server_error(exc):
        import logging

        logging.getLogger(__name__).exception(
            "Erro interno: %s", getattr(exc, "description", exc)
        )
        return jsonify({"error": "Erro interno do servidor."}), 500


def public_error_message(detail: str | None = None) -> dict:
    """Oculta detalhes internos em produção."""
    payload: dict = {"error": "Operação não concluída."}
    if detail and not Config.is_production():
        payload["detail"] = detail
    return payload


def ai_limit():
    return limiter.limit(Config.RATELIMIT_AI)
