"""Emissão e verificação de tokens de acesso.

Substitui `'fake-jwt-token-' + str(user.id)` de `routes/user_routes.py:210`:
um token não assinado, previsível a partir do id do usuário e que nenhum
endpoint validava. O token agora é um JWT HS256 assinado com a `SECRET_KEY`
e com expiração.
"""

from __future__ import annotations

from datetime import timedelta

import jwt

from ..exceptions import UnauthorizedError
from ..infrastructure.clock import utcnow

ALGORITHM = "HS256"

CLAIM_USER_ID = "sub"
CLAIM_ROLE = "role"

MESSAGE_EXPIRED = "Token expirado"
MESSAGE_INVALID = "Token inválido"


def issue_access_token(user, secret_key, expiration_minutes):
    issued_at = utcnow()
    payload = {
        # `sub` é string por convenção do RFC 7519.
        CLAIM_USER_ID: str(user.id),
        CLAIM_ROLE: user.role,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=expiration_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token, secret_key):
    """Devolve o payload do token ou levanta `UnauthorizedError`."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(MESSAGE_EXPIRED)
    except jwt.InvalidTokenError:
        raise UnauthorizedError(MESSAGE_INVALID)

    user_id = payload.get(CLAIM_USER_ID)
    if user_id is None:
        raise UnauthorizedError(MESSAGE_INVALID)

    try:
        payload[CLAIM_USER_ID] = int(user_id)
    except (TypeError, ValueError):
        raise UnauthorizedError(MESSAGE_INVALID)

    return payload
