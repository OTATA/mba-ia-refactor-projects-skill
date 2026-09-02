"""Cálculo dos relatórios.

`summary_report` (`routes/report_routes.py:12-101`) tinha 90 linhas e fazia:
12 `SELECT COUNT(*)` separados, um `Task.query.all()` que carregava a tabela
inteira para contar atrasadas em Python, e uma query por usuário para o
ranking de produtividade.

Aqui os mesmos números saem de agregações em SQL. O formato do JSON de saída
é idêntico ao original — inclusive os rótulos `critical`/`high`/`medium`/
`low`/`minimal` das prioridades e a ordem das chaves.
"""

from __future__ import annotations

from datetime import timedelta

from ..infrastructure.clock import utcnow
from ..models.enums import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    TaskStatus,
)
from ..repositories import category_repository, task_repository, user_repository
from .task_service import completion_rate

#: Janela de "atividade recente" do relatório.
RECENT_ACTIVITY_DAYS = 7


def _status_counts(by_status):
    return {status.value: by_status.get(status.value, 0) for status in TaskStatus}


def summary():
    """Payload de `GET /reports/summary`."""
    now = utcnow()
    recent_since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    by_status = task_repository.count_by_status()
    by_priority = task_repository.count_by_priority()
    overdue_tasks = task_repository.list_overdue(now)
    tasks_per_user = task_repository.status_breakdown_by_user()

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": task_repository.count_all(),
            "total_users": user_repository.count_all(),
            "total_categories": category_repository.count_all(),
        },
        "tasks_by_status": _status_counts(by_status),
        "tasks_by_priority": {
            label: by_priority.get(priority, 0)
            for priority, label in PRIORITY_LABELS.items()
        },
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": task.days_overdue(now),
                }
                for task in overdue_tasks
            ],
        },
        "recent_activity": {
            "tasks_created_last_7_days": task_repository.count_created_since(
                recent_since
            ),
            "tasks_completed_last_7_days": task_repository.count_completed_since(
                recent_since, TaskStatus.DONE.value
            ),
        },
        "user_productivity": _user_productivity(tasks_per_user),
    }


def _user_productivity(tasks_per_user):
    """Ranking de produtividade a partir do breakdown já agregado."""
    productivity = []
    for user in user_repository.list_all():
        counts = tasks_per_user.get(user.id, {})
        total = sum(counts.values())
        completed = counts.get(TaskStatus.DONE.value, 0)
        productivity.append(
            {
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": completion_rate(completed, total),
            }
        )
    return productivity


def for_user(user):
    """Payload de `GET /reports/user/<id>`."""
    now = utcnow()
    tasks = task_repository.list_by_user(user.id)

    counts = {status.value: 0 for status in TaskStatus}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
        if task.priority is not None and task.priority <= HIGH_PRIORITY_THRESHOLD:
            high_priority += 1
        if task.is_overdue(now):
            overdue += 1

    total = len(tasks)
    done = counts[TaskStatus.DONE.value]

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": counts[TaskStatus.PENDING.value],
            "in_progress": counts[TaskStatus.IN_PROGRESS.value],
            "cancelled": counts[TaskStatus.CANCELLED.value],
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": completion_rate(done, total),
        },
    }
