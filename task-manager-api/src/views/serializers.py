"""Transformação de entidades em payload público.

Esta é a camada de View da API: os models não decidem mais o próprio formato
de saída. Ela existe por dois motivos.

O primeiro é segurança. `User.to_dict()` incluía o campo `password`, e o
método era usado nas respostas de `GET /users/<id>`, `POST /users`,
`PUT /users/<id>` e `POST /login` — qualquer cliente recebia o hash de senha.
Aqui a lista de campos é explícita e `password` não está nela.

O segundo é que o original tinha três formatos diferentes para a mesma
entidade: `Task.to_dict()`, a reconstrução manual campo a campo em
`routes/task_routes.py:17-28`, e uma terceira variante parcial em
`routes/user_routes.py:162-169`. Cada endpoint mantém aqui o formato exato
que devolvia antes, mas agora num único lugar.

`str()` é usado nas datas — e não `.isoformat()` — para preservar byte a byte
o formato que os clientes já recebem (`2026-09-02 11:28:00.123456`). Migrar
para ISO 8601 é uma quebra de contrato e está registrada como achado LOW no
relatório de auditoria.
"""

from __future__ import annotations


def _format_datetime(value):
    return str(value) if value else None


def serialize_task(task):
    """Formato base de task, igual a `Task.to_dict()` do original."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "user_id": task.user_id,
        "category_id": task.category_id,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
        "due_date": _format_datetime(task.due_date),
        "tags": task.tag_list,
    }


def serialize_task_with_overdue(task, now=None):
    """Formato de `GET /tasks/<id>`: base + `overdue`."""
    data = serialize_task(task)
    data["overdue"] = task.is_overdue(now)
    return data


def serialize_task_listing(task, now=None):
    """Formato de `GET /tasks`: base + `overdue`, `user_name`, `category_name`.

    `user` e `category` já vêm carregados pelo eager loading do repository,
    então nenhuma query extra é disparada aqui.
    """
    data = serialize_task_with_overdue(task, now)
    data["user_name"] = task.user.name if task.user else None
    data["category_name"] = task.category.name if task.category else None
    return data


def serialize_user_task(task, now=None):
    """Formato reduzido de `GET /users/<id>/tasks`, igual ao original."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_at": str(task.created_at),
        "due_date": _format_datetime(task.due_date),
        "overdue": task.is_overdue(now),
    }


def serialize_user(user):
    """Formato público de usuário. Nunca inclui `password`."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "active": user.active,
        "created_at": str(user.created_at),
    }


def serialize_user_with_task_count(user, task_count):
    """Formato de `GET /users`: base + `task_count`."""
    data = serialize_user(user)
    data["task_count"] = task_count
    return data


def serialize_user_with_tasks(user, tasks):
    """Formato de `GET /users/<id>`: base + as tasks completas."""
    data = serialize_user(user)
    data["tasks"] = [serialize_task(task) for task in tasks]
    return data


def serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "created_at": str(category.created_at),
    }


def serialize_category_with_task_count(category, task_count):
    """Formato de `GET /categories`: base + `task_count`."""
    data = serialize_category(category)
    data["task_count"] = task_count
    return data


def serialize_collection(items, serializer, **kwargs):
    return [serializer(item, **kwargs) for item in items]
