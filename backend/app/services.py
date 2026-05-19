"""Integração com LLM, recomendações pedagógicas e regras de negócio."""

import json
import logging
import os
import re
import time
from datetime import date, timedelta
from math import ceil
from typing import Any

import httpx
from sqlalchemy import String, cast, or_

from app import db
from app.config import Config
from app.models import ClassPlan
from app.validators import ClassPlanCreateSchema

logger = logging.getLogger(__name__)

GROQ_CHAT_PATH = "/chat/completions"

RECOMMENDATIONS_SYSTEM_PROMPT = (
    "Você é um Assistente Pedagógico especializado em ensino superior. "
    "Sua função é sugerir conteúdos complementares, tópicos relacionados e tags "
    "relevantes para planos de aula. "
    "Responda ESTRITAMENTE em JSON válido, sem markdown, sem texto adicional, "
    "seguindo exatamente este formato: "
    '{"conteudos_complementares": ["item1", "item2"], '
    '"topicos_relacionados": ["topico1", "topico2"], '
    '"tags": ["tag1", "tag2", "tag3"]}. '
    "Todos os valores devem ser arrays de strings em português do Brasil."
)


class AIResponseError(Exception):
    """Resposta inválida ou incompleta da API de IA."""


class LLMService:
    """Cliente para geração e recomendações via Groq (API compatível com OpenAI)."""

    def __init__(self) -> None:
        self.model = os.getenv("GROQ_MODEL", Config.GROQ_MODEL)
        self.api_base = os.getenv("GROQ_API_BASE", Config.GROQ_API_BASE).rstrip("/")

    @property
    def api_key(self) -> str:
        return (os.getenv("GROQ_API_KEY") or "").strip()

    def get_recommendations(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = payload["title"]
        subject = payload["subject"]

        start = time.perf_counter()
        result, tokens, used_mock = self._recommendations_with_fallback(payload)
        latency = time.perf_counter() - start

        logger.info(
            f'AI Request: Title="{title}", Discipline="{subject}", '
            f"Token Usage={tokens}, Latency={latency:.1f}s."
        )
        if used_mock:
            logger.warning(
                "Recomendações servidas em modo mock (sem Groq ou API indisponível)."
            )

        return {**result, "fallback_mock": used_mock}

    def _recommendations_with_fallback(
        self, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], int, bool]:
        if not self.api_key:
            return self._mock_recommendations(payload), 0, True

        try:
            prompt = self._build_recommendations_prompt(payload)
            raw_text, tokens = self._call_groq(
                RECOMMENDATIONS_SYSTEM_PROMPT, prompt
            )
            parsed = self._parse_recommendations_json(raw_text)
            return parsed, tokens, False
        except (httpx.HTTPError, AIResponseError) as exc:
            if Config.ai_fallback_to_mock():
                logger.warning("Falha na API Groq (%s). Usando mock.", type(exc).__name__)
                return self._mock_recommendations(payload), 0, True
            raise

    def generate_class_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            return self._mock_plan(payload)

        prompt = self._build_prompt(payload)
        system = (
            "Você é um Assistente Pedagógico para professores do ensino superior. "
            "Gere planos de aula em português do Brasil. Responda APENAS com JSON válido, "
            "sem markdown, com as chaves: title, objective, syllabus_summary, "
            "scheduled_date (YYYY-MM-DD), subject, contents (array), "
            "support_resources (array), tags (array)."
        )
        try:
            raw_text, _tokens = self._call_groq(system, prompt)
            return self._parse_llm_json(raw_text)
        except (httpx.HTTPError, AIResponseError) as exc:
            if Config.ai_fallback_to_mock():
                logger.warning("Falha na API Groq (%s). Plano mock.", type(exc).__name__)
                return self._mock_plan(payload)
            raise

    def _call_groq(
        self, system_instruction: str, user_prompt: str
    ) -> tuple[str, int]:
        url = f"{self.api_base}{GROQ_CHAT_PATH}"
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise AIResponseError("Resposta da Groq sem conteúdo.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content or not isinstance(content, str):
            raise AIResponseError("Resposta da Groq inválida.")
        usage = data.get("usage") or {}
        tokens = int(usage.get("total_tokens", 0))
        return content, tokens

    def _build_recommendations_prompt(self, payload: dict[str, Any]) -> str:
        return (
            f'Com base no plano de aula abaixo, sugira conteúdos complementares, '
            f"tópicos relacionados e tags pedagógicas.\n\n"
            f'Título: {payload["title"]}\n'
            f'Disciplina: {payload["subject"]}\n'
            f'Ementa/Resumo: {payload["syllabus_summary"]}'
        )

    def _parse_recommendations_json(self, text: str) -> dict[str, Any]:
        data = self._parse_llm_json(text)
        required_keys = (
            "conteudos_complementares",
            "topicos_relacionados",
            "tags",
        )
        for key in required_keys:
            if key not in data:
                raise AIResponseError(
                    f"Resposta da IA incompleta: campo '{key}' ausente."
                )
            if not isinstance(data[key], list) or not all(
                isinstance(item, str) for item in data[key]
            ):
                raise AIResponseError(
                    f"Resposta da IA inválida: '{key}' deve ser uma lista de strings."
                )
        return {
            "conteudos_complementares": [
                s.strip() for s in data["conteudos_complementares"] if s.strip()
            ],
            "topicos_relacionados": [
                s.strip() for s in data["topicos_relacionados"] if s.strip()
            ],
            "tags": [s.strip() for s in data["tags"] if s.strip()],
        }

    def _mock_recommendations(self, payload: dict[str, Any]) -> dict[str, Any]:
        topic = payload["title"]
        subject = payload["subject"]
        return {
            "conteudos_complementares": [
                f"Material complementar sobre {topic}",
                "Estudo de caso prático",
                "Lista de exercícios resolvidos",
            ],
            "topicos_relacionados": [
                f"Fundamentos de {subject}",
                "Aplicações em cenários reais",
                "Revisão para avaliação",
            ],
            "tags": [subject.lower(), topic.lower()[:20], "ensino-superior"],
        }

    def _build_prompt(self, payload: dict[str, Any]) -> str:
        parts = [
            f"Crie um plano de aula para a disciplina {payload['subject']}.",
            f"Tema/título sugerido: {payload['topic']}.",
        ]
        if payload.get("objective"):
            parts.append(f"Objetivo informado: {payload['objective']}.")
        if payload.get("syllabus_summary"):
            parts.append(f"Ementa/resumo informado: {payload['syllabus_summary']}.")
        if payload.get("scheduled_date"):
            parts.append(f"Data prevista: {payload['scheduled_date']}.")
        if payload.get("contents"):
            parts.append(f"Conteúdos sugeridos: {', '.join(payload['contents'])}.")
        if payload.get("support_resources"):
            parts.append(
                f"Recursos sugeridos: {', '.join(payload['support_resources'])}."
            )
        if payload.get("tags"):
            parts.append(f"Tags sugeridas: {', '.join(payload['tags'])}.")
        return " ".join(parts)

    def _parse_llm_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIResponseError("A IA retornou um JSON inválido.") from exc

    def _mock_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        scheduled = payload.get("scheduled_date") or (
            date.today() + timedelta(days=7)
        )
        return {
            "title": payload["topic"],
            "objective": payload.get("objective")
            or f"Compreender os fundamentos de {payload['topic']}.",
            "syllabus_summary": (
                f"Aula sobre {payload['topic']} na disciplina {payload['subject']}."
            ),
            "scheduled_date": str(scheduled),
            "subject": payload["subject"],
            "contents": payload.get("contents")
            or [payload["topic"], "Exercícios práticos", "Discussão em grupo"],
            "support_resources": payload.get("support_resources")
            or ["Slides", "Quadro branco"],
            "tags": payload.get("tags") or [payload["subject"], "aula"],
        }


class ClassPlanService:
    """Regras de negócio para planos de aula."""

    def __init__(self) -> None:
        self.llm = LLMService()

    def get_recommendations(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.llm.get_recommendations(data)

    def create_plan(self, data: dict[str, Any]) -> ClassPlan:
        validated = ClassPlanCreateSchema.model_validate(data)
        plan = ClassPlan.from_payload(validated.model_dump())
        db.session.add(plan)
        db.session.commit()
        return plan

    def generate_and_save(self, data: dict[str, Any]) -> ClassPlan:
        generated = self.llm.generate_class_plan(data)
        merged = self._merge_generation(data, generated)
        validated = ClassPlanCreateSchema.model_validate(merged)
        plan = ClassPlan.from_payload(validated.model_dump())
        db.session.add(plan)
        db.session.commit()
        return plan

    def _merge_generation(
        self, input_data: dict[str, Any], generated: dict[str, Any]
    ) -> dict[str, Any]:
        scheduled = input_data.get("scheduled_date") or generated.get(
            "scheduled_date"
        )
        if isinstance(scheduled, str):
            scheduled = date.fromisoformat(scheduled)

        contents = input_data.get("contents") or generated.get("contents") or []
        support_resources = (
            input_data.get("support_resources")
            or generated.get("support_resources")
            or ["Material de apoio"]
        )
        tags = input_data.get("tags") or generated.get("tags") or [input_data["subject"]]

        return {
            "title": (generated.get("title") or input_data["topic"]).strip(),
            "objective": (
                input_data.get("objective") or generated.get("objective") or ""
            ).strip(),
            "syllabus_summary": (
                input_data.get("syllabus_summary")
                or generated.get("syllabus_summary")
                or ""
            ).strip(),
            "scheduled_date": scheduled or (date.today() + timedelta(days=7)),
            "subject": input_data["subject"],
            "contents": contents,
            "support_resources": support_resources,
            "tags": tags,
        }

    def list_plans(self, params: dict[str, Any]) -> dict[str, Any]:
        query = ClassPlan.query

        if params.get("subject"):
            query = query.filter(
                ClassPlan.subject.ilike(f"%{params['subject']}%")
            )

        if params.get("scheduled_date"):
            query = query.filter(
                ClassPlan.scheduled_date == params["scheduled_date"]
            )

        if params.get("search"):
            query = query.filter(
                ClassPlan.title.ilike(f"%{params['search']}%")
            )

        if params.get("tags"):
            tag_conditions = [
                cast(ClassPlan.tags, String).ilike(f'%"{tag}"%')
                for tag in params["tags"]
            ]
            query = query.filter(or_(*tag_conditions))

        sort_column = (
            ClassPlan.title
            if params.get("sort_by") == "title"
            else ClassPlan.created_at
        )
        if params.get("sort_order") == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        page = params["page"]
        per_page = params["per_page"]
        total = query.count()
        plans = query.offset((page - 1) * per_page).limit(per_page).all()

        total_pages = ceil(total / per_page) if total else 0

        return {
            "data": [plan.to_dict() for plan in plans],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    def get_plan(self, plan_id: int) -> ClassPlan | None:
        return db.session.get(ClassPlan, plan_id)

    def update_plan(self, plan: ClassPlan, data: dict[str, Any]) -> ClassPlan:
        list_fields = {"contents", "support_resources", "tags"}
        for key, value in data.items():
            if value is None:
                continue
            if key in list_fields:
                getattr(plan, f"set_{key}")(value)
            elif hasattr(plan, key):
                setattr(plan, key, value)
        db.session.commit()
        return plan

    def delete_plan(self, plan: ClassPlan) -> None:
        db.session.delete(plan)
        db.session.commit()
