"""Acesso a dados de Task.

Único lugar do projeto que constrói queries de task. No original havia 17
usos de `Task.query` espalhados por `routes/task_routes.py` e mais 23 em
`routes/report_routes.py`.

Duas correções de API depreciada:
- `Task.query` é interface legada no SQLAlchemy 2.0 → `db.session.execute(select(...))`
- `Task.query.get(id)` está depreciada desde a 2.0 → `db.session.get(Task, id)`

E duas de performance:
- `list_all` faz eager loading de user e category. `GET /tasks` disparava
  1 + 2N queries (1.001 queries para 500 tasks).
- as contagens viraram agregação em SQL. `summary_report` disparava 12
  `SELECT COUNT(*)` separados e carregava a tabela inteira em memória só
  para contar as atrasadas.
"""

from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models.enums import CLOSED_STATUSES
from ..models.task import Task

#: Escapa os wildcards de LIKE para que `%` e `_` digitados pelo usuário
#: sejam buscados literalmente. `Task.title.like(f'%{q}%')` no original
#: tratava `q='%'` como "tudo".
LIKE_ESCAPE_CHAR = "\\"


def _escape_like(term):
    escaped = term.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
    for wildcard in ("%", "_"):
        escaped = escaped.replace(wildcard, LIKE_ESCAPE_CHAR + wildcard)
    return f"%{escaped}%"


def _paginate(statement, limit=None, offset=None):
    if offset:
        statement = statement.offset(offset)
    if limit:
        statement = statement.limit(limit)
    return statement


def get(task_id):
    return db.session.get(Task, task_id)


def list_all(limit=None, offset=None):
    """Tasks com user e category já carregados (evita N+1)."""
    statement = (
        select(Task)
        .options(selectinload(Task.user), selectinload(Task.category))
        .order_by(Task.id)
    )
    return db.session.scalars(_paginate(statement, limit, offset)).all()


def list_by_user(user_id):
    statement = select(Task).where(Task.user_id == user_id).order_by(Task.id)
    return db.session.scalars(statement).all()


def search(term=None, status=None, priority=None, user_id=None, limit=None, offset=None):
    statement = select(Task)

    if term:
        pattern = _escape_like(term)
        # `ilike` em vez de `like`: a busca original era case-sensitive.
        statement = statement.where(
            or_(
                Task.title.ilike(pattern, escape=LIKE_ESCAPE_CHAR),
                Task.description.ilike(pattern, escape=LIKE_ESCAPE_CHAR),
            )
        )

    if status:
        statement = statement.where(Task.status == status)

    if priority is not None:
        statement = statement.where(Task.priority == priority)

    if user_id is not None:
        statement = statement.where(Task.user_id == user_id)

    statement = statement.order_by(Task.id)
    return db.session.scalars(_paginate(statement, limit, offset)).all()


def count_all():
    return db.session.scalar(select(func.count()).select_from(Task))


def count_by_status():
    """`{status: total}` num único GROUP BY, no lugar de 4 COUNTs."""
    rows = db.session.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    ).all()
    return {status: total for status, total in rows}


def count_by_priority():
    """`{priority: total}` num único GROUP BY, no lugar de 5 COUNTs."""
    rows = db.session.execute(
        select(Task.priority, func.count(Task.id)).group_by(Task.priority)
    ).all()
    return {priority: total for priority, total in rows}


def count_by_category():
    """`{category_id: total}`, no lugar de um COUNT por categoria."""
    rows = db.session.execute(
        select(Task.category_id, func.count(Task.id))
        .where(Task.category_id.is_not(None))
        .group_by(Task.category_id)
    ).all()
    return {category_id: total for category_id, total in rows}


def _overdue_condition(now):
    return and_(
        Task.due_date.is_not(None),
        Task.due_date < now,
        Task.status.not_in(CLOSED_STATUSES),
    )


def count_overdue(now):
    """Conta no banco, sem carregar a tabela para a memória."""
    return db.session.scalar(
        select(func.count()).select_from(Task).where(_overdue_condition(now))
    )


def list_overdue(now):
    # Ordenado por id para reproduzir a ordem em que `Task.query.all()`
    # devolvia as linhas no relatório original.
    statement = select(Task).where(_overdue_condition(now)).order_by(Task.id)
    return db.session.scalars(statement).all()


def count_created_since(moment):
    return db.session.scalar(
        select(func.count()).select_from(Task).where(Task.created_at >= moment)
    )


def count_completed_since(moment, done_status):
    return db.session.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.status == done_status, Task.updated_at >= moment)
    )


def status_breakdown_by_user():
    """`{user_id: {status: total}}` num único GROUP BY.

    `summary_report` disparava uma query por usuário para calcular isto.
    """
    rows = db.session.execute(
        select(Task.user_id, Task.status, func.count(Task.id))
        .where(Task.user_id.is_not(None))
        .group_by(Task.user_id, Task.status)
    ).all()

    breakdown = {}
    for user_id, status, total in rows:
        breakdown.setdefault(user_id, {})[status] = total
    return breakdown


def add(task):
    db.session.add(task)


def remove(task):
    db.session.delete(task)
