"""Configuração centralizada da aplicação."""

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///smart_class_plan.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 1_048_576))  # 1 MB

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080",
        ).split(",")
        if origin.strip()
    ]

    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "120 per minute")
    RATELIMIT_AI = os.getenv("RATELIMIT_AI", "10 per minute")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_API_BASE = os.getenv(
        "GROQ_API_BASE", "https://api.groq.com/openai/v1"
    ).rstrip("/")

    @classmethod
    def ai_fallback_to_mock(cls) -> bool:
        """Em dev, usa mock se a API Groq falhar (429, timeout, etc.)."""
        explicit = os.getenv("AI_FALLBACK_TO_MOCK", "").lower()
        if explicit == "true":
            return True
        if explicit == "false":
            return False
        return not cls.is_production()

    @staticmethod
    def is_production() -> bool:
        return os.getenv("FLASK_ENV", "development") == "production"

    @classmethod
    def validate_production(cls) -> None:
        if not cls.is_production():
            return
        if cls.SECRET_KEY in ("", "dev-secret-key", "change-me-in-production"):
            raise RuntimeError(
                "SECRET_KEY insegura em produção. Defina um valor aleatório forte."
            )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    GROQ_API_KEY = ""
    SECRET_KEY = "test-secret-key"
