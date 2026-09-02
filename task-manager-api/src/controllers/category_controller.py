"""Controller de categorias.

Estas quatro rotas viviam em `routes/report_routes.py` no original. As URLs
e os payloads não mudaram; apenas saíram do blueprint de relatórios.
"""

from __future__ import annotations

from ..services import category_service
from ..validators import category_validator
from ..views import responses, serializers
from .requests import read_json


def list_categories():
    categories = category_service.list_all()
    # Contagem agregada num GROUP BY, em vez de um COUNT por categoria.
    counts = category_service.task_counts()
    return responses.ok(
        [
            serializers.serialize_category_with_task_count(
                category, counts.get(category.id, 0)
            )
            for category in categories
        ]
    )


def create_category():
    payload = category_validator.validate_create_payload(read_json())
    category = category_service.create(payload)
    return responses.created(serializers.serialize_category(category))


def update_category(category_id):
    changes = category_validator.validate_update_payload(read_json())
    category = category_service.update(category_id, changes)
    return responses.ok(serializers.serialize_category(category))


def delete_category(category_id):
    category_service.delete(category_id)
    return responses.message("Categoria deletada")
