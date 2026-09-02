"""Regras de negócio de usuário.

Concentra o que estava dentro dos handlers de `routes/user_routes.py`:
unicidade de e-mail, hash da senha e fronteira transacional.

O loop que apagava as tasks do usuário à mão (`routes/user_routes.py:140-142`)
foi removido: a cascata agora está declarada no schema (`ON DELETE CASCADE`
no FK de `tasks.user_id`).
"""

from __future__ import annotations

import logging

from ..exceptions import ConflictError, NotFoundError
from ..models.user import User
from ..repositories import user_repository
from ..repositories.unit_of_work import commit_on_success

logger = logging.getLogger(__name__)

MESSAGE_USER_NOT_FOUND = "Usuário não encontrado"
MESSAGE_EMAIL_TAKEN = "Email já cadastrado"


def get(user_id):
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError(MESSAGE_USER_NOT_FOUND)
    return user


def list_all(limit=None, offset=None):
    return user_repository.list_all(limit=limit, offset=offset)


def task_counts():
    """`{user_id: total}` para o campo `task_count` de `GET /users`."""
    return user_repository.count_tasks_by_user()


def _require_email_available(email, current_user_id=None):
    existing = user_repository.find_by_email(email)
    if existing is not None and existing.id != current_user_id:
        raise ConflictError(MESSAGE_EMAIL_TAKEN)


def create(payload):
    """Cria o usuário. `payload` já vem validado pelo validator."""
    _require_email_available(payload["email"])

    user = User()
    user.name = payload["name"]
    user.email = payload["email"]
    user.set_password(payload["password"])
    user.assign_role(payload["role"])

    with commit_on_success():
        user_repository.add(user)

    logger.info("Usuário criado: id=%s name=%r", user.id, user.name)
    return user


def update(user_id, changes):
    """Aplica uma atualização parcial. `changes` só traz campos presentes."""
    user = get(user_id)

    if "email" in changes:
        _require_email_available(changes["email"], current_user_id=user_id)

    with commit_on_success():
        if "name" in changes:
            user.name = changes["name"]
        if "email" in changes:
            user.email = changes["email"]
        if "password" in changes:
            user.set_password(changes["password"])
        if "role" in changes:
            user.assign_role(changes["role"])
        if "active" in changes:
            user.active = changes["active"]

    logger.info("Usuário atualizado: id=%s", user.id)
    return user


def delete(user_id):
    user = get(user_id)

    with commit_on_success():
        user_repository.remove(user)

    logger.info("Usuário deletado: id=%s", user_id)
