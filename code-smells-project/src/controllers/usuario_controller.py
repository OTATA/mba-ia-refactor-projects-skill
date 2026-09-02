"""Controller de usuários e autenticação."""

from __future__ import annotations

from ..container import usuario_service
from ..views.responses import STATUS_CRIADO, resposta_sucesso
from ..views.serializers import (
    serializar_colecao,
    serializar_usuario,
    serializar_usuario_autenticado,
)
from .requests import ler_json


def listar():
    usuarios = usuario_service().listar()
    return resposta_sucesso(serializar_colecao(usuarios, serializar_usuario))


def buscar(usuario_id):
    usuario = usuario_service().buscar(usuario_id)
    return resposta_sucesso(serializar_usuario(usuario))


def criar():
    dados = ler_json()
    usuario_id = usuario_service().criar(
        nome=dados.get("nome", ""),
        email=dados.get("email", ""),
        senha=dados.get("senha", ""),
    )
    return resposta_sucesso({"id": usuario_id}, status=STATUS_CRIADO)


def login():
    dados = ler_json()
    usuario = usuario_service().autenticar(
        email=dados.get("email", ""), senha=dados.get("senha", "")
    )
    return resposta_sucesso(
        serializar_usuario_autenticado(usuario), mensagem="Login OK"
    )
