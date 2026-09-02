"""Entidade Category.

`to_dict()` saiu; a serialização vive em `src/views/serializers.py`.

A relação com Task declara `SET NULL`: `delete_category` no original apagava a
categoria e deixava `tasks.category_id` apontando para uma linha inexistente.
"""

from __future__ import annotations

from ..extensions import db
from ..infrastructure.clock import utcnow
from .enums import DEFAULT_COLOR


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship("Task", back_populates="category", passive_deletes=True)
