"""Acesso a dados de Category."""

from __future__ import annotations

from sqlalchemy import func, select

from ..extensions import db
from ..models.category import Category


def get(category_id):
    return db.session.get(Category, category_id)


def list_all():
    statement = select(Category).order_by(Category.id)
    return db.session.scalars(statement).all()


def count_all():
    return db.session.scalar(select(func.count()).select_from(Category))


def add(category):
    db.session.add(category)


def remove(category):
    db.session.delete(category)
