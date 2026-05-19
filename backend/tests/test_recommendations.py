"""Testes do endpoint de recomendações com IA (mock)."""

import httpx


def test_recommendations_without_api_key_uses_mock(client):
    response = client.post(
        "/api/plans/recommendations",
        json={
            "title": "Introdução ao OSPF",
            "subject": "Redes",
            "syllabus_summary": "Aula sobre roteamento dinâmico e protocolos.",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "conteudos_complementares" in body
    assert "topicos_relacionados" in body
    assert "tags" in body
    assert len(body["conteudos_complementares"]) >= 1
    assert len(body["tags"]) >= 1
    assert body.get("fallback_mock") is True


def test_recommendations_fallback_when_groq_fails(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-test")
    monkeypatch.setenv("AI_FALLBACK_TO_MOCK", "true")

    def _raise_429(*_args, **_kwargs):
        request = httpx.Request("POST", "https://example.com")
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("429", request=request, response=response)

    monkeypatch.setattr(
        "app.services.LLMService._call_groq",
        _raise_429,
    )

    response = client.post(
        "/api/plans/recommendations",
        json={
            "title": "Introdução ao OSPF",
            "subject": "Redes",
            "syllabus_summary": "Aula sobre roteamento dinâmico e protocolos.",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["fallback_mock"] is True
    assert len(body["conteudos_complementares"]) >= 1


def test_recommendations_rejects_missing_fields(client):
    response = client.post(
        "/api/plans/recommendations",
        json={"title": "Só título"},
    )
    assert response.status_code == 400


def test_recommendations_rejects_extra_fields(client):
    response = client.post(
        "/api/plans/recommendations",
        json={
            "title": "Introdução ao OSPF",
            "subject": "Redes",
            "syllabus_summary": "Ementa com conteúdo pedagógico válido.",
            "campo_extra": "hack",
        },
    )
    assert response.status_code == 400
