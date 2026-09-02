"""Tratamento centralizado de erros.

Substitui os 17 blocos `except Exception as e: return jsonify({"erro": str(e)})`
espalhados pelos handlers originais, que vazavam mensagens internas do SQLite
para o cliente e reportavam erro de requisição como HTTP 500.
"""

from __future__ import annotations

import logging
from http import HTTPStatus

from werkzeug.exceptions import HTTPException

from ..exceptions import DomainError
from ..views.responses import resposta_erro

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def registrar_error_handlers(app):
    @app.errorhandler(DomainError)
    def _erro_de_dominio(erro):
        return resposta_erro(erro.mensagem, erro.status_code)

    @app.errorhandler(HTTPException)
    def _erro_http(erro):
        return resposta_erro(erro.description, erro.code)

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        # O detalhe fica no log do servidor; o cliente recebe mensagem genérica.
        logger.exception("Falha inesperada ao processar a requisição: %s", erro)
        return resposta_erro(
            MENSAGEM_ERRO_INTERNO, HTTPStatus.INTERNAL_SERVER_ERROR
        )
