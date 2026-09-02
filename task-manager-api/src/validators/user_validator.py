"""Validação do payload de usuário.

Consolida as regras que estavam duplicadas entre `create_user`
(`routes/user_routes.py:61-72`) e `update_user` (`:106-122`), incluindo o
regex de e-mail que aparecia três vezes (nas duas rotas e em
`utils/helpers.validate_email`).

O regex é o original, sem alteração: ele aceita endereços sem TLD (`a@b`) e
isso está registrado como achado MEDIUM no relatório de auditoria — corrigi-lo
mudaria o conjunto de e-mails aceitos, ou seja, uma regra de negócio.
O mesmo vale para `MIN_PASSWORD_LENGTH = 4`.
"""

from __future__ import annotations

import re

from ..exceptions import ValidationError
from ..models.enums import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, UserRole

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")

MESSAGE_NAME_REQUIRED = "Nome é obrigatório"
MESSAGE_EMAIL_REQUIRED = "Email é obrigatório"
MESSAGE_PASSWORD_REQUIRED = "Senha é obrigatória"
MESSAGE_INVALID_EMAIL = "Email inválido"
MESSAGE_INVALID_ROLE = "Role inválido"
MESSAGE_INVALID_NAME = "Nome inválido"
MESSAGE_INVALID_ACTIVE = "Valor inválido para active"

#: `create_user` e `update_user` usavam mensagens diferentes para senha curta.
MESSAGE_PASSWORD_TOO_SHORT_ON_CREATE = "Senha deve ter no mínimo 4 caracteres"
MESSAGE_PASSWORD_TOO_SHORT_ON_UPDATE = "Senha muito curta"


def _validate_email(value):
    if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
        raise ValidationError(MESSAGE_INVALID_EMAIL)
    return value


def _validate_password(value, too_short_message):
    if not isinstance(value, str):
        raise ValidationError(too_short_message)
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return value


def _validate_role(value):
    if not UserRole.is_valid(value):
        raise ValidationError(MESSAGE_INVALID_ROLE)
    return value


def _validate_name(value):
    if not isinstance(value, str):
        raise ValidationError(MESSAGE_INVALID_NAME)
    return value


def validate_create_payload(data):
    """Normaliza o corpo de `POST /users`.

    Ordem preservada do original: presença dos três campos, formato do
    e-mail, tamanho da senha, e por fim o role. A unicidade do e-mail é
    uma regra de estado e fica no service.
    """
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name:
        raise ValidationError(MESSAGE_NAME_REQUIRED)
    if not email:
        raise ValidationError(MESSAGE_EMAIL_REQUIRED)
    if not password:
        raise ValidationError(MESSAGE_PASSWORD_REQUIRED)

    return {
        "name": _validate_name(name),
        "email": _validate_email(email),
        "password": _validate_password(
            password, MESSAGE_PASSWORD_TOO_SHORT_ON_CREATE
        ),
        "role": _validate_role(data.get("role", DEFAULT_ROLE)),
    }


def validate_update_payload(data):
    """Normaliza o corpo de `PUT /users/<id>` (atualização parcial)."""
    changes = {}

    if "name" in data:
        changes["name"] = _validate_name(data["name"])

    if "email" in data:
        changes["email"] = _validate_email(data["email"])

    if "password" in data:
        changes["password"] = _validate_password(
            data["password"], MESSAGE_PASSWORD_TOO_SHORT_ON_UPDATE
        )

    if "role" in data:
        changes["role"] = _validate_role(data["role"])

    if "active" in data:
        # O original aceitava qualquer valor e o gravava cru na coluna
        # booleana (`{"active": "no"}` virava um truthy no banco).
        if not isinstance(data["active"], bool):
            raise ValidationError(MESSAGE_INVALID_ACTIVE)
        changes["active"] = data["active"]

    return changes


def validate_credentials(data):
    """Extrai e-mail e senha de `POST /login`."""
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")

    return email, password
