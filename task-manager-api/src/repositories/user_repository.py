"""Acesso a dados de User.

`task_count` em `GET /users` vinha de `len(u.tasks)` (`routes/user_routes.py:22`),
que carregava a coleção inteira de tasks de cada usuário só para contá-la.
`count_tasks_by_user` resolve tudo num GROUP BY.
"""

from __future__ import annotations

from sqlalchemy import func, select

from ..extensions import db
from ..models.task import Task
from ..models.user import User


def get(user_id):
    return db.session.get(User, user_id)


def list_all(limit=None, offset=None):
    statement = select(User).order_by(User.id)
    if offset:
        statement = statement.offset(offset)
    if limit:
        statement = statement.limit(limit)
    return db.session.scalars(statement).all()


def find_by_email(email):
    statement = select(User).where(User.email == email)
    return db.session.scalars(statement).first()


def count_all():
    return db.session.scalar(select(func.count()).select_from(User))


def count_tasks_by_user():
    """`{user_id: total}` num único GROUP BY."""
    rows = db.session.execute(
        select(Task.user_id, func.count(Task.id))
        .where(Task.user_id.is_not(None))
        .group_by(Task.user_id)
    ).all()
    return {user_id: total for user_id, total in rows}


def add(user):
    db.session.add(user)


def remove(user):
    db.session.delete(user)
