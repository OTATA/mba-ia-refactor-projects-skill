"""Controller de usuários.

As respostas deixaram de conter o campo `password`: a serialização passa por
`views/serializers.serialize_user`, que tem lista de campos explícita.

`create_user` continua público — é o registro — mas a atribuição de um role
diferente de `user` agora exige um admin, o que fecha a escalação de
privilégio que existia em `PUT /users/<id>`.
"""

from __future__ import annotations

from ..exceptions import ForbiddenError
from ..infrastructure.clock import utcnow
from ..middlewares.auth import (
    MESSAGE_FORBIDDEN,
    current_user,
    require_admin_for_privileged_fields,
    require_self_or_admin,
)
from ..models.enums import DEFAULT_ROLE
from ..services import task_service, user_service
from ..validators import user_validator
from ..views import responses, serializers
from .requests import read_json, read_pagination


def list_users():
    limit, offset = read_pagination()
    users = user_service.list_all(limit=limit, offset=offset)
    # Contagem agregada num GROUP BY, em vez de um lazy-load por usuário.
    counts = user_service.task_counts()
    return responses.ok(
        [
            serializers.serialize_user_with_task_count(user, counts.get(user.id, 0))
            for user in users
        ]
    )


def get_user(user_id):
    user = user_service.get(user_id)
    tasks = task_service.list_by_user(user_id)
    return responses.ok(serializers.serialize_user_with_tasks(user, tasks))


def create_user():
    payload = user_validator.validate_create_payload(read_json())
    _require_admin_to_grant_role(payload["role"])
    user = user_service.create(payload)
    return responses.created(serializers.serialize_user(user))


def update_user(user_id):
    changes = user_validator.validate_update_payload(read_json())
    require_self_or_admin(user_id)
    require_admin_for_privileged_fields(changes)
    user = user_service.update(user_id, changes)
    return responses.ok(serializers.serialize_user(user))


def delete_user(user_id):
    user_service.delete(user_id)
    return responses.message("Usuário deletado com sucesso")


def list_user_tasks(user_id):
    user_service.get(user_id)
    tasks = task_service.list_by_user(user_id)
    now = utcnow()
    return responses.ok(
        serializers.serialize_collection(
            tasks, serializers.serialize_user_task, now=now
        )
    )


def _require_admin_to_grant_role(role):
    """Só um admin autenticado cria conta com role diferente de `user`."""
    if role == DEFAULT_ROLE:
        return

    author = current_user()
    if author is None or not author.is_admin:
        raise ForbiddenError(MESSAGE_FORBIDDEN)
