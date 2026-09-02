"""Construção do envelope de resposta da API.

Um único ponto define o formato, eliminando a inconsistência em que algumas
respostas de erro traziam `sucesso` e outras não.
"""

from __future__ import annotations

from http import HTTPStatus

from flask import jsonify

STATUS_OK = HTTPStatus.OK
STATUS_CRIADO = HTTPStatus.CREATED


def resposta_sucesso(dados=None, mensagem=None, status=STATUS_OK, **extras):
    corpo = {}
    if dados is not None:
        corpo["dados"] = dados
    corpo.update(extras)
    corpo["sucesso"] = True
    if mensagem is not None:
        corpo["mensagem"] = mensagem
    return jsonify(corpo), int(status)


def resposta_erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), int(status)
