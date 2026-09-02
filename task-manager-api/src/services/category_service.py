"""Regras de negócio de categoria.

No original estas quatro operações viviam em `routes/report_routes.py:157-223`
— categoria não é relatório. O CRUD agora tem controller e blueprint próprios,
com as mesmas URLs.
"""

from __future__ import annotations

import logging

from ..exceptions import NotFoundError
from ..models.category import Category
from ..repositories import category_repository, task_repository
from ..repositories.unit_of_work import commit_on_success

logger = logging.getLogger(__name__)

MESSAGE_CATEGORY_NOT_FOUND = "Categoria não encontrada"


def get(category_id):
    category = category_repository.get(category_id)
    if category is None:
        raise NotFoundError(MESSAGE_CATEGORY_NOT_FOUND)
    return category


def list_all():
    return category_repository.list_all()


def task_counts():
    """`{category_id: total}` para o campo `task_count` de `GET /categories`."""
    return task_repository.count_by_category()


def create(payload):
    category = Category()
    category.name = payload["name"]
    category.description = payload["description"]
    category.color = payload["color"]

    with commit_on_success():
        category_repository.add(category)

    logger.info("Categoria criada: id=%s name=%r", category.id, category.name)
    return category


def update(category_id, changes):
    category = get(category_id)

    with commit_on_success():
        for field, value in changes.items():
            setattr(category, field, value)

    logger.info("Categoria atualizada: id=%s", category.id)
    return category


def delete(category_id):
    """Remove a categoria. As tasks afetadas ficam com `category_id` nulo.

    O original deixava `tasks.category_id` apontando para uma linha
    inexistente; o `ON DELETE SET NULL` do schema evita o registro órfão.
    """
    category = get(category_id)

    with commit_on_success():
        category_repository.remove(category)

    logger.info("Categoria deletada: id=%s", category_id)
