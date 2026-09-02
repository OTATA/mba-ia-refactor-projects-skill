"""Validação do payload de categoria.

`update_category` (`routes/report_routes.py:196`) fazia `data = request.get_json()`
e ia direto para `if 'name' in data`: um corpo ausente virava `TypeError` e
HTTP 500. A leitura do corpo agora passa por `controllers/requests.ler_json`,
que devolve 400 "Dados inválidos".
"""

from __future__ import annotations

from ..exceptions import ValidationError
from ..models.enums import DEFAULT_COLOR

MESSAGE_NAME_REQUIRED = "Nome é obrigatório"
MESSAGE_INVALID_TEXT = "Valor de texto inválido"


def _validate_text(value, message=MESSAGE_INVALID_TEXT):
    if not isinstance(value, str):
        raise ValidationError(message)
    return value


def validate_create_payload(data):
    name = data.get("name")
    if not name:
        raise ValidationError(MESSAGE_NAME_REQUIRED)

    return {
        "name": _validate_text(name),
        "description": _validate_text(data.get("description", "")),
        "color": _validate_text(data.get("color", DEFAULT_COLOR)),
    }


def validate_update_payload(data):
    changes = {}

    for field in ("name", "description", "color"):
        if field in data:
            changes[field] = _validate_text(data[field])

    return changes
