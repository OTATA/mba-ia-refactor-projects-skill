"""Controller de produtos: entrada HTTP, delegação e escolha da resposta."""

from __future__ import annotations

from flask import request

from ..container import produto_service
from ..validators.produto_validator import validar_payload_produto
from ..views.responses import STATUS_CRIADO, resposta_sucesso
from ..views.serializers import serializar_colecao, serializar_produto
from .requests import ler_float_opcional, ler_json


def listar():
    produtos = produto_service().listar()
    return resposta_sucesso(serializar_colecao(produtos, serializar_produto))


def buscar(produto_id):
    produto = produto_service().buscar(produto_id)
    return resposta_sucesso(serializar_produto(produto))


def pesquisar():
    resultados = produto_service().pesquisar(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=ler_float_opcional("preco_min", "preco_min deve ser um número"),
        preco_max=ler_float_opcional("preco_max", "preco_max deve ser um número"),
    )
    dados = serializar_colecao(resultados, serializar_produto)
    return resposta_sucesso(dados, total=len(dados))


def criar():
    dados = validar_payload_produto(ler_json())
    produto_id = produto_service().criar(dados)
    return resposta_sucesso(
        {"id": produto_id}, mensagem="Produto criado", status=STATUS_CRIADO
    )


def atualizar(produto_id):
    dados = validar_payload_produto(ler_json())
    produto_service().atualizar(produto_id, dados)
    return resposta_sucesso(mensagem="Produto atualizado")


def deletar(produto_id):
    produto_service().deletar(produto_id)
    return resposta_sucesso(mensagem="Produto deletado")
