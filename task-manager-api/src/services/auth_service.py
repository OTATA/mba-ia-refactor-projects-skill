"""Autenticação e emissão de token.

`POST /login` (`routes/user_routes.py:185-211`) verificava as credenciais e
devolvia `'fake-jwt-token-' + str(user.id)`, que nenhum endpoint validava.
Agora emite um JWT assinado com expiração, e `identify` é o caminho que os
decorators de autorização usam para resolver o portador do token.

A ordem das checagens é a original: usuário existe → senha confere →
usuário está ativo. Um usuário inativo com a senha certa recebe 403,
e não 401.
"""

from __future__ import annotations

import logging

from flask import current_app

from ..exceptions import ForbiddenError, UnauthorizedError
from ..repositories import user_repository
from ..security.tokens import CLAIM_USER_ID, decode_access_token, issue_access_token

logger = logging.getLogger(__name__)

MESSAGE_INVALID_CREDENTIALS = "Credenciais inválidas"
MESSAGE_INACTIVE_USER = "Usuário inativo"


def _secret_key():
    return current_app.config["SECRET_KEY"]


def authenticate(email, password):
    """Valida as credenciais e devolve `(user, token)`."""
    user = user_repository.find_by_email(email)
    if user is None or not user.check_password(password):
        # Mensagem única para e-mail inexistente e senha errada: não revela
        # quais e-mails estão cadastrados.
        logger.info("Tentativa de login rejeitada para %r", email)
        raise UnauthorizedError(MESSAGE_INVALID_CREDENTIALS)

    if not user.active:
        raise ForbiddenError(MESSAGE_INACTIVE_USER)

    token = issue_access_token(
        user,
        _secret_key(),
        current_app.config["JWT_EXPIRATION_MINUTES"],
    )
    logger.info("Login realizado: user_id=%s", user.id)
    return user, token


def identify(token):
    """Resolve o usuário do token, ou levanta 401/403."""
    payload = decode_access_token(token, _secret_key())

    user = user_repository.get(payload[CLAIM_USER_ID])
    if user is None:
        raise UnauthorizedError(MESSAGE_INVALID_CREDENTIALS)

    # Um usuário desativado depois da emissão do token perde o acesso.
    if not user.active:
        raise ForbiddenError(MESSAGE_INACTIVE_USER)

    return user
