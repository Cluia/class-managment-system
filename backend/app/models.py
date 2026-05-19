"""Modelos do banco de dados."""

import json
from datetime import datetime, timezone
from typing import Any

from app import db


def parse_str_list(value: Any) -> list[str]:
    """Converte lista, JSON ou string separada por vírgula em lista de strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("JSON de lista inválido.") from exc
            if not isinstance(parsed, list):
                raise ValueError("JSON deve ser uma lista.")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in raw.split(",") if item.strip()]
    raise ValueError("Formato inválido para lista.")


class ClassPlan(db.Model):
    """Plano de aula — mapeamento da tabela principal."""

    __tablename__ = "class_plans"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # Título da Aula
    objective = db.Column(db.Text, nullable=False)  # Objetivo
    syllabus_summary = db.Column(db.Text, nullable=False)  # Ementa / Resumo
    scheduled_date = db.Column(db.Date, nullable=False)  # Data Prevista
    subject = db.Column(db.String(120), nullable=False)  # Disciplina
    contents = db.Column(db.JSON, nullable=False, default=list)  # Conteúdos
    support_resources = db.Column(
        db.JSON, nullable=False, default=list
    )  # Recursos de Apoio
    tags = db.Column(db.JSON, nullable=False, default=list)  # Tags
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_contents(self, value: Any) -> None:
        self.contents = parse_str_list(value)

    def set_support_resources(self, value: Any) -> None:
        self.support_resources = parse_str_list(value)

    def set_tags(self, value: Any) -> None:
        self.tags = parse_str_list(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "objective": self.objective,
            "syllabus_summary": self.syllabus_summary,
            "scheduled_date": (
                self.scheduled_date.isoformat() if self.scheduled_date else None
            ),
            "subject": self.subject,
            "contents": self.contents or [],
            "support_resources": self.support_resources or [],
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "ClassPlan":
        plan = cls(
            title=data["title"],
            objective=data["objective"],
            syllabus_summary=data["syllabus_summary"],
            scheduled_date=data["scheduled_date"],
            subject=data["subject"],
        )
        plan.set_contents(data.get("contents", []))
        plan.set_support_resources(data.get("support_resources", []))
        plan.set_tags(data.get("tags", []))
        return plan
