"""Testes de resiliência na integração Groq."""

import httpx


def test_recommendations_timeout_returns_504(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setenv("AI_FALLBACK_TO_MOCK", "false")

    def _timeout(*_args, **_kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("app.services.LLMService._call_groq", _timeout)

    response = client.post(
        "/api/plans/recommendations",
        json={
            "title": "Introdução ao OSPF",
            "subject": "Redes",
            "syllabus_summary": "Aula sobre roteamento dinâmico e protocolos.",
        },
    )
    assert response.status_code == 504
