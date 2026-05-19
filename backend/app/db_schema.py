"""Garante que class_plans corresponde ao modelo SQLAlchemy atual."""

import logging

from sqlalchemy import inspect, text

from app import db
from app.models import ClassPlan

logger = logging.getLogger(__name__)

# Colunas de uma versão anterior do projeto (schema incompatível com o modelo atual).
_LEGACY_COLUMNS = frozenset(
    {"grade_level", "duration_minutes", "objectives", "content", "status"}
)

# Colunas adicionadas depois da criação inicial (create_all não altera tabelas existentes).
_EXTRA_COLUMNS: dict[str, str] = {
    "objective": "TEXT NOT NULL DEFAULT ''",
    "syllabus_summary": "TEXT NOT NULL DEFAULT ''",
    "scheduled_date": "DATE",
    "contents": "JSON NOT NULL DEFAULT '[]'",
    "support_resources": "JSON NOT NULL DEFAULT '[]'",
    "tags": "JSON NOT NULL DEFAULT '[]'",
}


def sync_class_plans_schema() -> None:
    """Recria tabela legada ou adiciona colunas ausentes."""
    inspector = inspect(db.engine)
    if "class_plans" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("class_plans")}

    if _LEGACY_COLUMNS & existing:
        logger.warning(
            "Schema legado em class_plans detectado (%s). Recriando tabela.",
            ", ".join(sorted(_LEGACY_COLUMNS & existing)),
        )
        ClassPlan.__table__.drop(db.engine)
        db.create_all()
        return

    dialect = db.engine.dialect.name
    for name, ddl in _EXTRA_COLUMNS.items():
        if name in existing:
            continue
        column_ddl = _adapt_column_ddl(ddl, dialect)
        stmt = text(f"ALTER TABLE class_plans ADD COLUMN {name} {column_ddl}")
        logger.info("Migrando schema: ADD COLUMN class_plans.%s", name)
        db.session.execute(stmt)

    db.session.commit()


def _adapt_column_ddl(ddl: str, dialect: str) -> str:
    if dialect == "sqlite":
        return ddl.replace(" NOT NULL", "").replace("JSON", "TEXT")
    if dialect == "postgresql":
        return ddl.replace("JSON", "JSONB")
    return ddl
