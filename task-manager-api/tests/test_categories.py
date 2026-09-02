"""Contrato dos 4 endpoints de categoria.

As URLs são as mesmas de antes, embora os handlers tenham saído do blueprint
de relatórios.
"""

from __future__ import annotations

from src.extensions import db

from .conftest import make_task

CATEGORY_BASE_FIELDS = {"id", "name", "description", "color", "created_at"}


def test_list_categories_traz_task_count(client, app, seeded, member_headers):
    with app.app_context():
        make_task("T1", category_id=seeded["category_id"])
        make_task("T2", category_id=seeded["category_id"])
        make_task("Sem categoria")
        db.session.commit()

    response = client.get("/categories", headers=member_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert set(body[0]) == CATEGORY_BASE_FIELDS | {"task_count"}
    assert body[0]["task_count"] == 2


def test_create_category_aplica_os_defaults(client, member_headers):
    response = client.post(
        "/categories", headers=member_headers, json={"name": "Nova"}
    )

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == CATEGORY_BASE_FIELDS
    assert body["name"] == "Nova"
    assert body["description"] == ""
    assert body["color"] == "#000000"


def test_create_category_sem_nome(client, member_headers):
    response = client.post("/categories", headers=member_headers, json={"color": "#fff"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Nome é obrigatório"}


def test_create_category_com_corpo_vazio(client, member_headers):
    response = client.post("/categories", headers=member_headers, json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Dados inválidos"}


def test_update_category(client, seeded, member_headers):
    response = client.put(
        f"/categories/{seeded['category_id']}",
        headers=member_headers,
        json={"name": "Renomeada", "color": "#ffffff"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Renomeada"
    assert body["color"] == "#ffffff"


def test_update_category_sem_corpo_devolve_400_e_nao_500(
    client, seeded, member_headers
):
    """No original, `if 'name' in None` levantava TypeError e virava HTTP 500."""
    response = client.put(
        f"/categories/{seeded['category_id']}", headers=member_headers
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Dados inválidos"}


def test_update_category_inexistente(client, member_headers):
    response = client.put("/categories/9999", headers=member_headers, json={"name": "X"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "Categoria não encontrada"}


def test_delete_category(client, seeded, member_headers):
    response = client.delete(
        f"/categories/{seeded['category_id']}", headers=member_headers
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Categoria deletada"}


def test_delete_category_deixa_as_tasks_sem_fk_orfa(
    client, app, seeded, member_headers
):
    """No original a task ficava apontando para uma categoria inexistente."""
    with app.app_context():
        make_task("Task categorizada", category_id=seeded["category_id"])
        db.session.commit()

    client.delete(f"/categories/{seeded['category_id']}", headers=member_headers)

    tasks = client.get("/tasks", headers=member_headers).get_json()
    assert tasks[0]["category_id"] is None
    assert tasks[0]["category_name"] is None


def test_delete_category_inexistente(client, member_headers):
    response = client.delete("/categories/9999", headers=member_headers)

    assert response.status_code == 404
