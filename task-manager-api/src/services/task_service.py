"""Regras de negócio de task.

Concentra o que estava dentro dos handlers de `routes/task_routes.py`:
existência das referências, aplicação das mudanças e fronteira transacional.
O service não conhece `request`, `jsonify` nem status HTTP.
"""

from __future__ import annotations

import logging

from ..exceptions import NotFoundError
from ..infrastructure.clock import utcnow
from ..models.enums import TaskStatus
from ..models.task import Task
from ..repositories import category_repository, task_repository, user_repository
from ..repositories.unit_of_work import commit_on_success

logger = logging.getLogger(__name__)

MESSAGE_TASK_NOT_FOUND = "Task não encontrada"
MESSAGE_USER_NOT_FOUND = "Usuário não encontrado"
MESSAGE_CATEGORY_NOT_FOUND = "Categoria não encontrada"

#: Campos que o cliente pode alterar via `PUT /tasks/<id>`.
UPDATABLE_FIELDS = (
    "title",
    "description",
    "status",
    "priority",
    "user_id",
    "category_id",
    "due_date",
    "tags",
)


def _require_user(user_id):
    if user_id is None:
        return
    if user_repository.get(user_id) is None:
        raise NotFoundError(MESSAGE_USER_NOT_FOUND)


def _require_category(category_id):
    if category_id is None:
        return
    if category_repository.get(category_id) is None:
        raise NotFoundError(MESSAGE_CATEGORY_NOT_FOUND)


def get(task_id):
    task = task_repository.get(task_id)
    if task is None:
        raise NotFoundError(MESSAGE_TASK_NOT_FOUND)
    return task


def list_all(limit=None, offset=None):
    return task_repository.list_all(limit=limit, offset=offset)


def list_by_user(user_id):
    return task_repository.list_by_user(user_id)


def search(term=None, status=None, priority=None, user_id=None, limit=None, offset=None):
    return task_repository.search(
        term=term,
        status=status,
        priority=priority,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


def create(payload):
    """Cria a task. `payload` já vem validado pelo validator."""
    _require_user(payload["user_id"])
    _require_category(payload["category_id"])

    task = Task()
    for field in UPDATABLE_FIELDS:
        setattr(task, field, payload[field])

    with commit_on_success():
        task_repository.add(task)

    logger.info("Task criada: id=%s title=%r", task.id, task.title)
    return task


def update(task_id, changes):
    """Aplica uma atualização parcial. `changes` só traz campos presentes."""
    task = get(task_id)

    if "user_id" in changes:
        _require_user(changes["user_id"])
    if "category_id" in changes:
        _require_category(changes["category_id"])

    with commit_on_success():
        for field, value in changes.items():
            setattr(task, field, value)
        # `updated_at` não é atribuído à mão: o `onupdate` do model já cuida,
        # e o original mantinha as duas coisas.

    logger.info("Task atualizada: id=%s", task.id)
    return task


def delete(task_id):
    task = get(task_id)

    with commit_on_success():
        task_repository.remove(task)

    logger.info("Task deletada: id=%s", task_id)


def stats():
    """Contadores de `GET /tasks/stats`, agregados no banco."""
    total = task_repository.count_all()
    by_status = task_repository.count_by_status()
    done = by_status.get(TaskStatus.DONE.value, 0)

    return {
        "total": total,
        "pending": by_status.get(TaskStatus.PENDING.value, 0),
        "in_progress": by_status.get(TaskStatus.IN_PROGRESS.value, 0),
        "done": done,
        "cancelled": by_status.get(TaskStatus.CANCELLED.value, 0),
        "overdue": task_repository.count_overdue(utcnow()),
        "completion_rate": completion_rate(done, total),
    }


def completion_rate(completed, total):
    """Percentual de conclusão com duas casas, ou 0 quando não há tasks."""
    if total <= 0:
        return 0
    return round((completed / total) * 100, 2)
