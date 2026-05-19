"""Factory da aplicação Flask."""

import os
from typing import Type

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

from app.config import Config, TestConfig  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

setup_logging()

db = SQLAlchemy()


def create_app(config_class: Type[Config] | None = None) -> Flask:
    app = Flask(__name__)

    cfg = config_class or Config
    app.config.from_object(cfg)
    cfg.validate_production()

    from app.security import init_security

    init_security(app)
    db.init_app(app)

    from app.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()
        from app.db_schema import sync_class_plans_schema

        sync_class_plans_schema()

    return app


def create_test_app() -> Flask:
    os.environ["FLASK_ENV"] = "testing"
    os.environ["GROQ_API_KEY"] = ""
    os.environ["RATELIMIT_ENABLED"] = "false"
    return create_app(TestConfig)
