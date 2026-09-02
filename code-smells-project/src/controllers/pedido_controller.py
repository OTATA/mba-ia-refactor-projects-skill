"""Controller de pedidos."""

from __future__ import annotations

from ..container import pedido_service
from ..views.responses import STATUS_CRIADO, resposta_sucesso
from ..views.serializers import serializar_colecao, serializar_pedido
from .requests import ler_json


def criar():
    dados = ler_json()
    resultado = pedido_service().criar(
        usuario_id=dados.get("usuario_id"), itens_payload=dados.get("itens", [])
    )
    return resposta_sucesso(
        resultado, mensagem="Pedido criado com sucesso", status=STATUS_CRIADO
    )


def listar_todos():
    pedidos = pedido_service().listar()
    return resposta_sucesso(serializar_colecao(pedidos, serializar_pedido))


def listar_por_usuario(usuario_id):
    pedidos = pedido_service().listar(usuario_id)
    return resposta_sucesso(serializar_colecao(pedidos, serializar_pedido))


def atualizar_status(pedido_id):
    dados = ler_json()
    pedido_service().atualizar_status(pedido_id, dados.get("status", ""))
    return resposta_sucesso(mensagem="Status atualizado")
