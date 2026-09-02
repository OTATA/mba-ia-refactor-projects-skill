"""Contrato dos 7 endpoints de task.

Os formatos de resposta e as mensagens de erro conferidos aqui são os do
código original, para que a refatoração possa ser verificada e não apenas
revisada.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from src.extensions import db
from src.infrastructure.clock import utcnow

from .conftest import make_task

TASK_BASE_FIELDS = {
    "id",
    "title",
    "description",
    "status",
    "priority",
    "user_id",
    "category_id",
    "created_at",
    "updated_at",
    "due_date",
    "tags",
}


@pytest.fixture
def task_id(app, seeded):
    with app.app_context():
        task = make_task(
            "Tarefa existente",
            description="descrição",
            status="pending",
            priority=2,
            user_id=seeded["member_id"],
            category_id=seeded["category_id"],
            tags="a,b",
        )
        db.session.commit()
        return task.id


def test_list_tasks_traz_overdue_user_name_e_category_name(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task(
            "Atrasada",
            status="pending",
            user_id=seeded["member_id"],
            category_id=seeded["category_id"],
            due_date=utcnow() - timedelta(days=2),
        )
        db.session.commit()

    response = client.get("/tasks", headers=member_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert set(body[0]) == TASK_BASE_FIELDS | {
        "overdue",
        "user_name",
        "category_name",
    }
    assert body[0]["overdue"] is True
    assert body[0]["user_name"] == "Membro"
    assert body[0]["category_name"] == "Backend"


def test_task_concluida_com_prazo_vencido_nao_esta_overdue(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task(
            "Entregue com atraso",
            status="done",
            due_date=utcnow() - timedelta(days=5),
        )
        db.session.commit()

    body = client.get("/tasks", headers=member_headers).get_json()

    assert body[0]["overdue"] is False


def test_get_task_traz_overdue(client, task_id, member_headers):
    response = client.get(f"/tasks/{task_id}", headers=member_headers)

    assert response.status_code == 200
    assert set(response.get_json()) == TASK_BASE_FIELDS | {"overdue"}


def test_get_task_inexistente(client, member_headers):
    response = client.get("/tasks/9999", headers=member_headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Task não encontrada"}


def test_create_task_devolve_201_e_o_formato_base(client, seeded, member_headers):
    response = client.post(
        "/tasks",
        headers=member_headers,
        json={
            "title": "Nova task",
            "description": "detalhe",
            "priority": 1,
            "user_id": seeded["member_id"],
            "category_id": seeded["category_id"],
            "due_date": "2030-12-31",
            "tags": ["x", "y"],
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == TASK_BASE_FIELDS
    assert body["title"] == "Nova task"
    assert body["status"] == "pending"
    assert body["tags"] == ["x", "y"]


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({}, 400, "Dados inválidos"),
        ({"description": "sem título"}, 400, "Título é obrigatório"),
        ({"title": "ab"}, 400, "Título muito curto"),
        ({"title": "x" * 201}, 400, "Título muito longo"),
        ({"title": "válido", "status": "unknown"}, 400, "Status inválido"),
        (
            {"title": "válido", "priority": 0},
            400,
            "Prioridade deve ser entre 1 e 5",
        ),
        (
            {"title": "válido", "priority": 6},
            400,
            "Prioridade deve ser entre 1 e 5",
        ),
        ({"title": "válido", "user_id": 9999}, 404, "Usuário não encontrado"),
        (
            {"title": "válido", "category_id": 9999},
            404,
            "Categoria não encontrada",
        ),
        (
            {"title": "válido", "due_date": "31/12/2030"},
            400,
            "Formato de data inválido. Use YYYY-MM-DD",
        ),
    ],
)
def test_create_task_rejeita_payload_invalido(
    client, member_headers, payload, status, message
):
    response = client.post("/tasks", headers=member_headers, json=payload)

    assert response.status_code == status
    assert response.get_json() == {"error": message}


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "válido", "priority": "alta"},
        {"title": "válido", "priority": None},
    ],
)
def test_priority_de_tipo_errado_devolve_400_e_nao_500(
    client, member_headers, payload
):
    """No original, `priority < 1` levantava TypeError e virava HTTP 500."""
    response = client.post("/tasks", headers=member_headers, json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Prioridade inválida"


def test_update_task_aplica_mudanca_parcial(client, task_id, member_headers):
    response = client.put(
        f"/tasks/{task_id}",
        headers=member_headers,
        json={"status": "done", "tags": ["novo"]},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == TASK_BASE_FIELDS
    assert body["status"] == "done"
    assert body["tags"] == ["novo"]
    assert body["title"] == "Tarefa existente"


def test_update_task_usa_a_mensagem_de_data_original(
    client, task_id, member_headers
):
    response = client.put(
        f"/tasks/{task_id}", headers=member_headers, json={"due_date": "ontem"}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Formato de data inválido"}


def test_update_task_com_titulo_nulo_devolve_400_e_nao_500(
    client, task_id, member_headers
):
    """No original, `len(None)` levantava TypeError e virava HTTP 500."""
    response = client.put(
        f"/tasks/{task_id}", headers=member_headers, json={"title": None}
    )

    assert response.status_code == 400


def test_update_task_permite_desatribuir_usuario(client, task_id, member_headers):
    response = client.put(
        f"/tasks/{task_id}", headers=member_headers, json={"user_id": None}
    )

    assert response.status_code == 200
    assert response.get_json()["user_id"] is None


def test_update_task_inexistente(client, member_headers):
    response = client.put("/tasks/9999", headers=member_headers, json={"title": "abc"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "Task não encontrada"}


def test_delete_task(client, task_id, member_headers):
    response = client.delete(f"/tasks/{task_id}", headers=member_headers)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Task deletada com sucesso"}
    assert client.get(f"/tasks/{task_id}", headers=member_headers).status_code == 404


def test_delete_task_inexistente(client, member_headers):
    response = client.delete("/tasks/9999", headers=member_headers)

    assert response.status_code == 404


def test_search_filtra_por_termo_status_prioridade_e_usuario(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task("Corrigir bug de login", status="pending", priority=1,
                  user_id=seeded["member_id"])
        make_task("Escrever documentação", status="done", priority=4,
                  user_id=seeded["admin_id"])
        db.session.commit()

    por_termo = client.get("/tasks/search?q=bug", headers=member_headers).get_json()
    assert [task["title"] for task in por_termo] == ["Corrigir bug de login"]

    por_status = client.get(
        "/tasks/search?status=done", headers=member_headers
    ).get_json()
    assert [task["title"] for task in por_status] == ["Escrever documentação"]

    por_prioridade = client.get(
        "/tasks/search?priority=1", headers=member_headers
    ).get_json()
    assert len(por_prioridade) == 1

    por_usuario = client.get(
        f"/tasks/search?user_id={seeded['admin_id']}", headers=member_headers
    ).get_json()
    assert len(por_usuario) == 1


def test_search_ignora_case_e_trata_wildcard_como_literal(
    client, app, seeded, member_headers
):
    """`like(f'%{q}%')` no original era case-sensitive e tratava `%` como curinga."""
    with app.app_context():
        make_task("Reduzir 100% do lixo")
        make_task("Outra tarefa")
        db.session.commit()

    assert len(client.get("/tasks/search?q=REDUZIR", headers=member_headers).get_json()) == 1
    assert len(client.get("/tasks/search?q=100%", headers=member_headers).get_json()) == 1


def test_search_com_prioridade_nao_numerica_devolve_400_e_nao_500(
    client, member_headers
):
    """No original, `int('abc')` levantava ValueError sem try e virava HTTP 500."""
    response = client.get("/tasks/search?priority=abc", headers=member_headers)

    assert response.status_code == 400


def test_stats_conta_por_status_e_calcula_completion_rate(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task("A", status="done")
        make_task("B", status="done")
        make_task("C", status="pending")
        make_task("D", status="in_progress")
        make_task("E", status="cancelled",
                  due_date=utcnow() - timedelta(days=1))
        make_task("F", status="pending", due_date=utcnow() - timedelta(days=1))
        db.session.commit()

    body = client.get("/tasks/stats", headers=member_headers).get_json()

    assert body == {
        "total": 6,
        "pending": 2,
        "in_progress": 1,
        "done": 2,
        "cancelled": 1,
        # Só a pendente vencida conta; a cancelada não.
        "overdue": 1,
        "completion_rate": 33.33,
    }


def test_stats_com_banco_vazio_nao_divide_por_zero(client, seeded, member_headers):
    body = client.get("/tasks/stats", headers=member_headers).get_json()

    assert body["total"] == 0
    assert body["completion_rate"] == 0


def test_paginacao_opcional_nao_altera_o_padrao(client, app, seeded, member_headers):
    with app.app_context():
        for index in range(5):
            make_task(f"Task {index}")
        db.session.commit()

    assert len(client.get("/tasks", headers=member_headers).get_json()) == 5
    assert len(client.get("/tasks?limit=2", headers=member_headers).get_json()) == 2
    assert (
        len(client.get("/tasks?limit=2&offset=4", headers=member_headers).get_json())
        == 1
    )
