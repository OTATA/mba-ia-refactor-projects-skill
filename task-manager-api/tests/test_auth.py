"""Contrato de `POST /login` e da autorização aplicada às rotas.

O original não tinha autorização nenhuma: qualquer anônimo alcançava as 22
rotas. Estes testes fixam a política declarada em `src/views/routes.py`.
"""

from __future__ import annotations

import jwt
import pytest

from src.security.tokens import ALGORITHM

from .conftest import TEST_SECRET_KEY


def test_login_devolve_message_user_e_token(client, seeded):
    response = client.post(
        "/login", json={"email": "admin@email.com", "password": "1234"}
    )

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"message", "user", "token"}
    assert body["message"] == "Login realizado com sucesso"
    assert "password" not in body["user"]


def test_o_token_e_um_jwt_assinado_e_nao_o_id_do_usuario(client, seeded):
    """No original o token era `'fake-jwt-token-' + str(user.id)`."""
    body = client.post(
        "/login", json={"email": "admin@email.com", "password": "1234"}
    ).get_json()

    payload = jwt.decode(body["token"], TEST_SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == str(seeded["admin_id"])
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_token_assinado_com_outra_chave_e_rejeitado(client, seeded):
    forjado = jwt.encode(
        {"sub": "1", "role": "admin"},
        "outra-chave-de-tamanho-suficiente-para-hs256",
        algorithm=ALGORITHM,
    )

    response = client.get("/users", headers={"Authorization": f"Bearer {forjado}"})

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({}, 400, "Dados inválidos"),
        ({"email": "admin@email.com"}, 400, "Email e senha são obrigatórios"),
        ({"password": "1234"}, 400, "Email e senha são obrigatórios"),
        (
            {"email": "ninguem@email.com", "password": "1234"},
            401,
            "Credenciais inválidas",
        ),
        (
            {"email": "admin@email.com", "password": "errada"},
            401,
            "Credenciais inválidas",
        ),
        (
            {"email": "inativo@email.com", "password": "pass"},
            403,
            "Usuário inativo",
        ),
    ],
)
def test_login_rejeita_credencial_invalida(client, seeded, payload, status, message):
    response = client.post("/login", json=payload)

    assert response.status_code == status
    assert response.get_json() == {"error": message}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/tasks"),
        ("get", "/tasks/1"),
        ("post", "/tasks"),
        ("put", "/tasks/1"),
        ("delete", "/tasks/1"),
        ("get", "/tasks/search"),
        ("get", "/tasks/stats"),
        ("get", "/users"),
        ("get", "/users/1"),
        ("put", "/users/1"),
        ("delete", "/users/1"),
        ("get", "/users/1/tasks"),
        ("get", "/categories"),
        ("post", "/categories"),
        ("put", "/categories/1"),
        ("delete", "/categories/1"),
        ("get", "/reports/summary"),
        ("get", "/reports/user/1"),
    ],
)
def test_rotas_protegidas_exigem_token(client, seeded, method, path):
    response = getattr(client, method)(path, json={})

    assert response.status_code == 401
    assert response.get_json() == {"error": "Autenticação obrigatória"}


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/"), ("get", "/health"), ("post", "/login"), ("post", "/users")],
)
def test_rotas_publicas_nao_exigem_token(client, seeded, method, path):
    response = getattr(client, method)(path, json={})

    assert response.status_code != 401


def test_header_authorization_malformado(client, seeded):
    response = client.get("/tasks", headers={"Authorization": "Token abc"})

    assert response.status_code == 401


def test_usuario_desativado_perde_o_acesso_com_token_ja_emitido(
    client, seeded, admin_headers, member_headers
):
    assert client.get("/tasks", headers=member_headers).status_code == 200

    client.put(
        f"/users/{seeded['member_id']}", headers=admin_headers, json={"active": False}
    )

    response = client.get("/tasks", headers=member_headers)
    assert response.status_code == 403
    assert response.get_json() == {"error": "Usuário inativo"}
