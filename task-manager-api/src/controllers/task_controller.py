"""Controller de tasks: entrada HTTP, delegação e escolha da resposta.

Compare com `routes/task_routes.py`, onde `create_task` tinha 70 linhas e
`update_task` 68, ambas misturando validação, regra de negócio, query e
serialização. Aqui cada handler tem o mesmo formato: ler entrada, validar
forma, delegar, serializar.
"""

from __future__ import annotations

from flask import request

from ..infrastructure.clock import utcnow
from ..services import task_service
from ..validators import task_validator
from ..views import responses, serializers
from .requests import (
    MESSAGE_INVALID_PRIORITY,
    MESSAGE_INVALID_USER,
    read_json,
    read_optional_int,
    read_pagination,
)


def list_tasks():
    limit, offset = read_pagination()
    tasks = task_service.list_all(limit=limit, offset=offset)
    now = utcnow()
    return responses.ok(
        serializers.serialize_collection(
            tasks, serializers.serialize_task_listing, now=now
        )
    )


def get_task(task_id):
    task = task_service.get(task_id)
    return responses.ok(serializers.serialize_task_with_overdue(task, utcnow()))


def create_task():
    payload = task_validator.validate_create_payload(read_json())
    task = task_service.create(payload)
    return responses.created(serializers.serialize_task(task))


def update_task(task_id):
    changes = task_validator.validate_update_payload(read_json())
    task = task_service.update(task_id, changes)
    return responses.ok(serializers.serialize_task(task))


def delete_task(task_id):
    task_service.delete(task_id)
    return responses.message("Task deletada com sucesso")


def search_tasks():
    limit, offset = read_pagination()
    tasks = task_service.search(
        term=request.args.get("q", ""),
        status=request.args.get("status", ""),
        priority=read_optional_int("priority", MESSAGE_INVALID_PRIORITY),
        user_id=read_optional_int("user_id", MESSAGE_INVALID_USER),
        limit=limit,
        offset=offset,
    )
    return responses.ok(
        serializers.serialize_collection(tasks, serializers.serialize_task)
    )


def task_stats():
    return responses.ok(task_service.stats())
