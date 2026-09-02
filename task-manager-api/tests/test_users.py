"""Contrato dos 5 endpoints de usuário."""

from __future__ import annotations

from datetime import timedelta

import pytest

from src.extensions import db
from src.infrastructure.clock import utcnow

from .conftest import make_task

USER_BASE_FIELDS = {"id", "name", "email", "role", "active", "created_at"}


def test_list_users_traz_task_count_e_nunca_password(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task("T1", user_id=seeded["member_id"])
        make_task("T2", user_id=seeded["member_id"])
        db.session.commit()

    response = client.get("/users", headers=member_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 3
    assert set(body[0]) == USER_BASE_FIELDS | {"task_count"}
    counts = {user["email"]: user["task_count"] for user in body}
    assert counts["membro@email.com"] == 2
    assert counts["admin@email.com"] == 0


def test_get_user_embute_as_tasks_e_nunca_password(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task("Minha task", user_id=seeded["member_id"])
        db.session.commit()

    response = client.get(f"/users/{seeded['member_id']}", headers=member_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == USER_BASE_FIELDS | {"tasks"}
    assert [task["title"] for task in body["tasks"]] == ["Minha task"]


def test_get_user_inexistente(client, member_headers):
    response = client.get("/users/9999", headers=member_headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Usuário não encontrado"}


def test_create_user_devolve_201_sem_password(client):
    """`POST /users` é o registro e continua público, como no original."""
    response = client.post(
        "/users",
        json={"name": "Nova", "email": "nova@email.com", "password": "1234"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == USER_BASE_FIELDS
    assert "password" not in body
    assert body["role"] == "user"
    assert body["active"] is True


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({}, 400, "Dados inválidos"),
        ({"email": "a@b.com", "password": "1234"}, 400, "Nome é obrigatório"),
        ({"name": "N", "password": "1234"}, 400, "Email é obrigatório"),
        ({"name": "N", "email": "a@b.com"}, 400, "Senha é obrigatória"),
        (
            {"name": "N", "email": "invalido", "password": "1234"},
            400,
            "Email inválido",
        ),
        (
            {"name": "N", "email": "a@b.com", "password": "123"},
            400,
            "Senha deve ter no mínimo 4 caracteres",
        ),
    ],
)
def test_create_user_rejeita_payload_invalido(client, payload, status, message):
    response = client.post("/users", json=payload)

    assert response.status_code == status
    assert response.get_json() == {"error": message}


def test_create_user_com_email_duplicado_devolve_409(client, seeded):
    response = client.post(
        "/users",
        json={"name": "Outro", "email": "admin@email.com", "password": "1234"},
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Email já cadastrado"}


def test_registro_anonimo_nao_pode_criar_admin(client):
    """Fecha a criação de conta privilegiada por quem não é admin."""
    response = client.post(
        "/users",
        json={
            "name": "Intruso",
            "email": "intruso@email.com",
            "password": "1234",
            "role": "admin",
        },
    )

    assert response.status_code == 403


def test_admin_pode_criar_conta_com_role_privilegiado(client, admin_headers):
    response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Gerente",
            "email": "gerente@email.com",
            "password": "1234",
            "role": "manager",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["role"] == "manager"


def test_create_user_com_role_invalido(client, admin_headers):
    response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "N",
            "email": "n@email.com",
            "password": "1234",
            "role": "root",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Role inválido"}


def test_update_user_altera_o_proprio_perfil(client, seeded, member_headers):
    response = client.put(
        f"/users/{seeded['member_id']}",
        headers=member_headers,
        json={"name": "Membro Renomeado"},
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "Membro Renomeado"


def test_update_user_troca_a_senha_e_o_login_passa_a_usar_a_nova(
    client, seeded, member_headers
):
    assert (
        client.put(
            f"/users/{seeded['member_id']}",
            headers=member_headers,
            json={"password": "senha-nova"},
        ).status_code
        == 200
    )

    assert (
        client.post(
            "/login", json={"email": "membro@email.com", "password": "abcd"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/login", json={"email": "membro@email.com", "password": "senha-nova"}
        ).status_code
        == 200
    )


def test_update_user_senha_curta_usa_a_mensagem_do_update(
    client, seeded, member_headers
):
    response = client.put(
        f"/users/{seeded['member_id']}", headers=member_headers, json={"password": "1"}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Senha muito curta"}


def test_update_user_email_duplicado_devolve_409(client, seeded, member_headers):
    response = client.put(
        f"/users/{seeded['member_id']}",
        headers=member_headers,
        json={"email": "admin@email.com"},
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Email já cadastrado"}


def test_update_user_com_o_proprio_email_e_permitido(client, seeded, member_headers):
    response = client.put(
        f"/users/{seeded['member_id']}",
        headers=member_headers,
        json={"email": "membro@email.com"},
    )

    assert response.status_code == 200


def test_usuario_comum_nao_se_promove_a_admin(client, seeded, member_headers):
    """Este era o vetor de escalação de privilégio do original."""
    response = client.put(
        f"/users/{seeded['member_id']}",
        headers=member_headers,
        json={"role": "admin"},
    )

    assert response.status_code == 403
    assert client.get(f"/users/{seeded['member_id']}", headers=member_headers).get_json()[
        "role"
    ] == "user"


def test_usuario_comum_nao_edita_perfil_alheio(client, seeded, member_headers):
    response = client.put(
        f"/users/{seeded['admin_id']}", headers=member_headers, json={"name": "Hackeado"}
    )

    assert response.status_code == 403


def test_admin_pode_alterar_role_e_active(client, seeded, admin_headers):
    response = client.put(
        f"/users/{seeded['member_id']}",
        headers=admin_headers,
        json={"role": "manager", "active": False},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["role"] == "manager"
    assert body["active"] is False


def test_delete_user_exige_admin(client, seeded, member_headers):
    response = client.delete(f"/users/{seeded['admin_id']}", headers=member_headers)

    assert response.status_code == 403


def test_admin_deleta_usuario_e_as_tasks_vao_em_cascata(
    client, app, seeded, admin_headers, member_headers
):
    with app.app_context():
        make_task("Task do membro", user_id=seeded["member_id"])
        db.session.commit()

    response = client.delete(f"/users/{seeded['member_id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Usuário deletado com sucesso"}
    assert client.get("/tasks", headers=admin_headers).get_json() == []


def test_delete_user_inexistente(client, admin_headers):
    response = client.delete("/users/9999", headers=admin_headers)

    assert response.status_code == 404


def test_user_tasks_usa_o_formato_reduzido_original(
    client, app, seeded, member_headers
):
    with app.app_context():
        make_task(
            "Atrasada",
            user_id=seeded["member_id"],
            due_date=utcnow() - timedelta(days=1),
        )
        db.session.commit()

    response = client.get(
        f"/users/{seeded['member_id']}/tasks", headers=member_headers
    )

    assert response.status_code == 200
    body = response.get_json()
    assert set(body[0]) == {
        "id",
        "title",
        "description",
        "status",
        "priority",
        "created_at",
        "due_date",
        "overdue",
    }
    assert body[0]["overdue"] is True


def test_user_tasks_de_usuario_inexistente(client, member_headers):
    response = client.get("/users/9999/tasks", headers=member_headers)

    assert response.status_code == 404
