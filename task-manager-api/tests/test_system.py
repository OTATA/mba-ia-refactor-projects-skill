"""Rotas de sistema, tratamento de erros e as garantias de segurança.

Estes testes cobrem o que não é endpoint de domínio: o boot, o error handler
centralizado e as duas correções de segurança que não têm rota própria (hash
de senha e ausência do campo `password` nas respostas).
"""

from __future__ import annotations

import pytest

from src.app import create_app
from src.config.settings import load_settings
from src.extensions import db
from src.models.user import User
from src.security.passwords import hash_password, verify_password


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Task Manager API", "version": "1.0"}


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["timestamp"]


def test_a_aplicacao_sobe_sem_erros(settings):
    assert create_app(settings) is not None


def test_rota_inexistente_devolve_json_e_nao_html(client):
    """O 404 do Werkzeug vinha em HTML; agora passa pelo error handler."""
    response = client.get("/nao-existe")

    assert response.status_code == 404
    assert response.is_json
    assert "error" in response.get_json()


def test_metodo_nao_permitido_devolve_json(client, member_headers):
    response = client.patch("/tasks", headers=member_headers, json={})

    assert response.status_code == 405
    assert response.is_json


def test_json_malformado_devolve_400_e_nao_500(client, member_headers):
    response = client.post(
        "/tasks",
        headers={**member_headers, "Content-Type": "application/json"},
        data="{isso não é json",
    )

    assert response.status_code == 400
    assert response.is_json


def test_secret_key_obrigatoria_em_producao():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_settings({"APP_ENV": "production"})


def test_settings_gera_chave_efemera_em_desenvolvimento():
    assert load_settings({"APP_ENV": "development"}).secret_key


def test_a_senha_nao_e_gravada_em_texto_claro_nem_em_md5(app):
    """MD5 tem 32 caracteres hex; o hash atual é scrypt com salt."""
    with app.app_context():
        user = User()
        user.name = "Teste"
        user.email = "hash@email.com"
        user.set_password("segredo")
        db.session.add(user)
        db.session.commit()

        assert user.password != "segredo"
        assert not (len(user.password) == 32 and all(
            char in "0123456789abcdef" for char in user.password
        ))
        assert user.password.startswith("scrypt:")


def test_o_mesmo_texto_gera_hashes_diferentes(app):
    """Salt por senha: dois usuários com a mesma senha não colidem."""
    assert hash_password("igual") != hash_password("igual")


def test_verificacao_de_senha(app):
    stored = hash_password("correta")

    assert verify_password(stored, "correta")
    assert not verify_password(stored, "errada")


def test_hash_md5_legado_nao_derruba_a_verificacao(app):
    """Um banco não migrado devolve 401, não HTTP 500."""
    md5_legado = "5f4dcc3b5aa765d61d8327deb882cf99"

    assert not verify_password(md5_legado, "password")


@pytest.mark.parametrize(
    ("method", "path_template"),
    [
        ("get", "/users"),
        ("get", "/users/{member_id}"),
        ("get", "/reports/summary"),
    ],
)
def test_nenhuma_resposta_expoe_o_campo_password(
    client, seeded, member_headers, method, path_template
):
    response = getattr(client, method)(
        path_template.format(**seeded), headers=member_headers
    )

    assert response.status_code == 200
    assert "password" not in response.get_data(as_text=True)


def test_secret_key_curta_e_recusada_em_producao():
    """HS256 exige chave de 256 bits (RFC 7518 §3.2)."""
    with pytest.raises(RuntimeError, match="ao menos 32 caracteres"):
        load_settings({"APP_ENV": "production", "SECRET_KEY": "curta"})
