"""Autenticação e autorização por requisição.

O original não tinha nada disto: nenhuma das 22 rotas verificava identidade.
Um anônimo podia listar todos os usuários, apagar qualquer usuário e suas
tasks, e se promover a admin com um `PUT /users/<id>` contendo
`{"role": "admin"}` (`routes/user_routes.py:119-122`). `User.is_admin()`
existia no model e nunca era chamado.

Os decorators leem o `Authorization: Bearer <token>`, resolvem o usuário e o
expõem em `g.current_user`. A política de acesso está declarada em
`src/views/routes.py`, para ficar visível junto das URLs.
"""

from __future__ import annotations

from functools import wraps

from flask import g, request

from ..exceptions import ForbiddenError, UnauthorizedError
from ..models.enums import UserRole
from ..services import auth_service

AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "

MESSAGE_MISSING_TOKEN = "Autenticação obrigatória"
MESSAGE_FORBIDDEN = "Acesso negado"


def _read_bearer_token():
    header = request.headers.get(AUTHORIZATION_HEADER, "")
    if not header.startswith(BEARER_PREFIX):
        raise UnauthorizedError(MESSAGE_MISSING_TOKEN)

    token = header[len(BEARER_PREFIX) :].strip()
    if not token:
        raise UnauthorizedError(MESSAGE_MISSING_TOKEN)
    return token


def current_user():
    """Usuário autenticado da requisição, ou `None` em rota pública."""
    return getattr(g, "current_user", None)


def require_auth(view):
    """Exige um token válido e publica o portador em `g.current_user`."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = auth_service.identify(_read_bearer_token())
        return view(*args, **kwargs)

    return wrapper


def optional_auth(view):
    """Resolve o portador do token quando houver, sem exigir um.

    Usado no registro (`POST /users`), que é público mas precisa saber se
    quem chamou é um admin para permitir a criação de conta privilegiada.
    Um token presente e inválido continua sendo rejeitado.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = None
        if request.headers.get(AUTHORIZATION_HEADER):
            g.current_user = auth_service.identify(_read_bearer_token())
        return view(*args, **kwargs)

    return wrapper


def require_role(*roles):
    """Exige um token válido cujo portador tenha um dos papéis informados."""
    allowed = frozenset(role.value if isinstance(role, UserRole) else role for role in roles)

    def decorator(view):
        @wraps(view)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.current_user.role not in allowed:
                raise ForbiddenError(MESSAGE_FORBIDDEN)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_self_or_admin(user_id):
    """Autoriza a operação apenas para o próprio usuário ou para um admin.

    Fecha a edição de perfil alheio, que o original permitia a qualquer um.
    """
    user = current_user()
    if user is None:
        raise UnauthorizedError(MESSAGE_MISSING_TOKEN)
    if user.id != user_id and not user.is_admin:
        raise ForbiddenError(MESSAGE_FORBIDDEN)


def require_admin_for_privileged_fields(changes):
    """`role` e `active` só podem ser alterados por um admin.

    É esta regra que fecha a escalação de privilégio: sem ela, o dono de uma
    conta comum podia se tornar admin editando o próprio perfil.
    """
    privileged = {"role", "active"} & set(changes)
    if not privileged:
        return

    user = current_user()
    if user is None or not user.is_admin:
        raise ForbiddenError(MESSAGE_FORBIDDEN)
