"""Testes dos endpoints CRUD e listagem."""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "database": "connected",
    }


def test_health_has_security_headers(client):
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_create_plan(client, sample_plan_data):
    response = client.post("/api/plans", json=sample_plan_data)
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == sample_plan_data["title"]
    assert body["subject"] == "Redes"


def test_create_plan_rejects_invalid_json(client):
    response = client.post(
        "/api/plans",
        data="nao-e-json",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_create_plan_rejects_empty_required_fields(client, sample_plan_data):
    payload = {**sample_plan_data, "title": "  "}
    response = client.post("/api/plans", json=payload)
    assert response.status_code == 400


def test_get_plan_not_found(client):
    response = client.get("/api/plans/9999")
    assert response.status_code == 404


def test_update_and_delete_plan(client, created_plan):
    plan_id = created_plan["id"]

    response = client.put(
        f"/api/plans/{plan_id}",
        json={"title": "OSPF Avançado"},
    )
    assert response.status_code == 200
    assert response.get_json()["title"] == "OSPF Avançado"

    response = client.delete(f"/api/plans/{plan_id}")
    assert response.status_code == 204

    response = client.get(f"/api/plans/{plan_id}")
    assert response.status_code == 404


def test_list_plans_pagination(client, created_plan):
    response = client.get("/api/plans?page=1&per_page=5")
    assert response.status_code == 200
    body = response.get_json()
    assert "data" in body
    assert "pagination" in body
    assert body["pagination"]["total"] >= 1


def test_list_plans_filter_by_subject(client, created_plan):
    response = client.get("/api/plans?subject=Redes")
    assert response.status_code == 200
    plans = response.get_json()["data"]
    assert all("Redes" in p["subject"] for p in plans)


def test_list_plans_search_by_title(client, created_plan):
    response = client.get("/api/plans?search=OSPF")
    assert response.status_code == 200
    plans = response.get_json()["data"]
    assert len(plans) >= 1
    assert any("OSPF" in p["title"] for p in plans)


def test_list_plans_sort_by_title(client, created_plan, sample_plan_data):
    client.post(
        "/api/plans",
        json={
            **sample_plan_data,
            "title": "AAA Primeira Aula",
            "scheduled_date": "2026-07-01",
        },
    )
    response = client.get("/api/plans?sort_by=title&sort_order=asc")
    assert response.status_code == 200
    titles = [p["title"] for p in response.get_json()["data"]]
    assert titles == sorted(titles)
