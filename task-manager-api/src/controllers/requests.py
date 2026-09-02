"""Leitura de entrada HTTP compartilhada pelos controllers."""

from __future__ import annotations

from flask import request

from ..exceptions import ValidationError

MESSAGE_INVALID_BODY = "Dados inválidos"
MESSAGE_INVALID_PRIORITY = "Prioridade inválida"
MESSAGE_INVALID_USER = "Usuário inválido"
MESSAGE_INVALID_PAGINATION = "Parâmetro de paginação inválido"


def read_json():
    """Corpo JSON da requisição, ou 400.

    `silent=True` evita que um corpo ausente ou malformado escape como
    exceção não tratada — o que em `update_category` virava HTTP 500.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        raise ValidationError(MESSAGE_INVALID_BODY)
    return data


def read_optional_int(name, message):
    """Query param inteiro, ou `None`.

    No original, `?priority=abc` levantava `ValueError` em `int(priority)` e
    devolvia HTTP 500; agora é 400.
    """
    raw = request.args.get(name)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(message)


def read_pagination():
    """`limit`/`offset` opcionais.

    Sem os parâmetros o comportamento é o de antes: a listagem completa. O
    relatório de auditoria recomenda um limite máximo por padrão, o que
    truncaria respostas já em uso e por isso ficou como passo seguinte.
    """
    limit = read_optional_int("limit", MESSAGE_INVALID_PAGINATION)
    offset = read_optional_int("offset", MESSAGE_INVALID_PAGINATION)

    if (limit is not None and limit < 0) or (offset is not None and offset < 0):
        raise ValidationError(MESSAGE_INVALID_PAGINATION)

    return limit, offset
