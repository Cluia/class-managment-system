"""Validação de dados com Pydantic."""

from datetime import date
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.models import parse_str_list

REQUIRED_LIST_MIN = 1
REQUIRED_LIST_MSG = "Informe ao menos um item."


def _coerce_list(value: Any) -> list[str]:
    return parse_str_list(value)


def _strip_required(value: str, field_label: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_label} é obrigatório e não pode estar vazio.")
    return stripped


def _strip_optional(value: Optional[str], field_label: str) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_label} não pode estar vazio.")
    return stripped


def _validate_non_empty_items(items: list[str], field_label: str) -> list[str]:
    if not items:
        raise ValueError(f"{field_label}: {REQUIRED_LIST_MSG}")
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        raise ValueError(f"{field_label}: {REQUIRED_LIST_MSG}")
    return cleaned


NonEmptyStrList = Annotated[
    list[str],
    Field(min_length=REQUIRED_LIST_MIN, description="Lista com ao menos um item."),
]


class ClassPlanCreateSchema(BaseModel):
    """Schema de cadastro — todos os campos obrigatórios."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(..., min_length=3, max_length=255)
    objective: str = Field(..., min_length=3, max_length=2000)
    syllabus_summary: str = Field(..., min_length=3, max_length=5000)
    scheduled_date: date
    subject: str = Field(..., min_length=2, max_length=120)
    contents: NonEmptyStrList
    support_resources: NonEmptyStrList
    tags: NonEmptyStrList

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_required(value, "Título da aula")

    @field_validator("objective")
    @classmethod
    def validate_objective(cls, value: str) -> str:
        return _strip_required(value, "Objetivo")

    @field_validator("syllabus_summary")
    @classmethod
    def validate_syllabus_summary(cls, value: str) -> str:
        return _strip_required(value, "Ementa/Resumo")

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        return _strip_required(value, "Disciplina")

    @field_validator("contents", "support_resources", "tags", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        return _coerce_list(value)

    @field_validator("contents")
    @classmethod
    def validate_contents(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_items(value, "Conteúdos")

    @field_validator("support_resources")
    @classmethod
    def validate_support_resources(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_items(value, "Recursos de apoio")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_items(value, "Tags")


class ClassPlanUpdateSchema(BaseModel):
    """Schema de edição — ao menos um campo; valores enviados não podem ser vazios."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    objective: Optional[str] = Field(None, min_length=3, max_length=2000)
    syllabus_summary: Optional[str] = Field(None, min_length=3, max_length=5000)
    scheduled_date: Optional[date] = None
    subject: Optional[str] = Field(None, min_length=2, max_length=120)
    contents: Optional[list[str]] = None
    support_resources: Optional[list[str]] = None
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value, "Título da aula")

    @field_validator("objective")
    @classmethod
    def validate_objective(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value, "Objetivo")

    @field_validator("syllabus_summary")
    @classmethod
    def validate_syllabus_summary(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value, "Ementa/Resumo")

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value, "Disciplina")

    @field_validator("contents", "support_resources", "tags", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> Optional[list[str]]:
        if value is None:
            return None
        return _coerce_list(value)

    @field_validator("contents")
    @classmethod
    def validate_contents(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        return _validate_non_empty_items(value, "Conteúdos")

    @field_validator("support_resources")
    @classmethod
    def validate_support_resources(
        cls, value: Optional[list[str]]
    ) -> Optional[list[str]]:
        if value is None:
            return None
        return _validate_non_empty_items(value, "Recursos de apoio")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        return _validate_non_empty_items(value, "Tags")

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ClassPlanUpdateSchema":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Informe ao menos um campo para atualização.")
        return self


class GeneratePlanSchema(BaseModel):
    """Schema para geração via LLM — campos mínimos obrigatórios."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject: str = Field(..., min_length=2, max_length=120)
    topic: str = Field(..., min_length=3, max_length=255)
    objective: Optional[str] = Field(None, max_length=2000)
    syllabus_summary: Optional[str] = Field(None, max_length=5000)
    scheduled_date: Optional[date] = None
    contents: Optional[list[str]] = None
    support_resources: Optional[list[str]] = None
    tags: Optional[list[str]] = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        return _strip_required(value, "Disciplina")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        return _strip_required(value, "Tema/Título")

    @field_validator("objective", "syllabus_summary")
    @classmethod
    def validate_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _strip_optional(value, "Campo textual")

    @field_validator("contents", "support_resources", "tags", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> Optional[list[str]]:
        if value is None:
            return None
        parsed = _coerce_list(value)
        return parsed or None

    @field_validator("contents", "support_resources", "tags")
    @classmethod
    def validate_optional_lists(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        return _validate_non_empty_items(value, "Lista")


class RecommendationsSchema(BaseModel):
    """Entrada para recomendações pedagógicas via IA."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(..., min_length=3, max_length=255)
    subject: str = Field(..., min_length=2, max_length=120)
    syllabus_summary: str = Field(..., min_length=3, max_length=5000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_required(value, "Título da aula")

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        return _strip_required(value, "Disciplina")

    @field_validator("syllabus_summary")
    @classmethod
    def validate_syllabus_summary(cls, value: str) -> str:
        return _strip_required(value, "Ementa/Resumo")


class PlanListQuerySchema(BaseModel):
    """Query params para listagem paginada de planos."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    subject: Optional[str] = Field(None, max_length=120)
    tags: Optional[list[str]] = None
    scheduled_date: Optional[date] = None
    search: Optional[str] = Field(None, max_length=255)
    sort_by: Literal["title", "created_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator("subject", "search")
    @classmethod
    def strip_optional_filter(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags_filter(cls, value: Any) -> Optional[list[str]]:
        if value is None or value == "" or value == []:
            return None
        parsed = _coerce_list(value)
        return parsed or None


def format_validation_errors(exc: ValidationError) -> dict[str, Any]:
    """Formata erros do Pydantic para resposta JSON da API."""
    errors = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(part) for part in loc if part != "body")
        message = err.get("msg", "Valor inválido.")
        if err.get("type") == "value_error":
            ctx = err.get("ctx", {})
            if "error" in ctx:
                message = str(ctx["error"])
        errors.append({"field": field or "body", "message": message})

    return {
        "error": "Dados inválidos.",
        "errors": errors,
    }
