"""Tratamento centralizado de erros.

Substitui os 12 blocos `except:` nus do original. Um `except:` sem classe
captura `BaseException` — inclusive `KeyboardInterrupt` e `SystemExit` — e os
handlers devolviam HTTP 500 com mensagem genérica e **sem log**: em
`routes/task_routes.py:62-63` todo o `GET /tasks` estava embrulhado assim, o
que transformava qualquer bug num "Erro interno" invisível.

Agora o detalhe fica no log do servidor, com stack trace, e o cliente recebe
o status correto: 400/401/403/404/409 para falhas esperadas e 500 apenas
para o que é realmente inesperado.
"""

from __future__ import annotations

import logging
from http import HTTPStatus

from werkzeug.exceptions import HTTPException

from ..exceptions import DomainError
from ..views.responses import error

logger = logging.getLogger(__name__)

MESSAGE_INTERNAL_ERROR = "Erro interno"
MESSAGE_NOT_FOUND = "Recurso não encontrado"


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def _domain_error(exc):
        logger.info("Requisição recusada (%s): %s", exc.status_code, exc.message)
        return error(exc.message, exc.status_code)

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        # Cobre 404 de rota inexistente, 405 de método errado e 400 de JSON
        # malformado, que antes escapavam como HTML do Werkzeug.
        description = exc.description or MESSAGE_NOT_FOUND
        return error(description, exc.code)

    @app.errorhandler(Exception)
    def _unexpected_error(exc):
        logger.exception("Falha inesperada ao processar a requisição: %s", exc)
        return error(MESSAGE_INTERNAL_ERROR, HTTPStatus.INTERNAL_SERVER_ERROR)
