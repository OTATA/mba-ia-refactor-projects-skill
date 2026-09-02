"""Contrato dos 2 endpoints de relatório.

O formato do JSON — chaves, aninhamento e os rótulos das prioridades — é o
mesmo produzido pelas 90 linhas de `summary_report` no original, embora os
números agora venham de agregações em SQL.
"""

from __future__ import annotations

from datetime import timedelta

from src.extensions import db
from src.infrastructure.clock import utcnow

from .conftest import make_task


def _populate(seeded):
    now = utcnow()
    make_task("Feita", status="done", priority=1, user_id=seeded["member_id"])
    make_task("Pendente", status="pending", priority=2, user_id=seeded["member_id"])
    make_task(
        "Atrasada",
        status="pending",
        priority=3,
        user_id=seeded["admin_id"],
        due_date=now - timedelta(days=4),
    )
    make_task("Cancelada", status="cancelled", priority=5)
    db.session.commit()


def test_summary_mantem_a_estrutura_original(client, app, seeded, member_headers):
    with app.app_context():
        _populate(seeded)

    response = client.get("/reports/summary", headers=member_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {
        "generated_at",
        "overview",
        "tasks_by_status",
        "tasks_by_priority",
        "overdue",
        "recent_activity",
        "user_productivity",
    }
    assert body["overview"] == {
        "total_tasks": 4,
        "total_users": 3,
        "total_categories": 1,
    }
    assert body["tasks_by_status"] == {
        "pending": 2,
        "in_progress": 0,
        "done": 1,
        "cancelled": 1,
    }
    assert body["tasks_by_priority"] == {
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 0,
        "minimal": 1,
    }


def test_summary_lista_as_atrasadas_com_dias_de_atraso(
    client, app, seeded, member_headers
):
    with app.app_context():
        _populate(seeded)

    overdue = client.get("/reports/summary", headers=member_headers).get_json()["overdue"]

    assert overdue["count"] == 1
    assert set(overdue["tasks"][0]) == {"id", "title", "due_date", "days_overdue"}
    assert overdue["tasks"][0]["title"] == "Atrasada"
    assert overdue["tasks"][0]["days_overdue"] == 4


def test_summary_conta_atividade_dos_ultimos_7_dias(
    client, app, seeded, member_headers
):
    with app.app_context():
        _populate(seeded)

    activity = client.get("/reports/summary", headers=member_headers).get_json()[
        "recent_activity"
    ]

    # As quatro tasks foram criadas agora; uma delas está com status `done`.
    assert activity["tasks_created_last_7_days"] == 4
    assert activity["tasks_completed_last_7_days"] == 1


def test_summary_lista_todos_os_usuarios_inclusive_sem_tasks(
    client, app, seeded, member_headers
):
    with app.app_context():
        _populate(seeded)

    productivity = client.get("/reports/summary", headers=member_headers).get_json()[
        "user_productivity"
    ]

    assert len(productivity) == 3
    por_nome = {entry["user_name"]: entry for entry in productivity}
    assert por_nome["Membro"]["total_tasks"] == 2
    assert por_nome["Membro"]["completed_tasks"] == 1
    assert por_nome["Membro"]["completion_rate"] == 50.0
    assert por_nome["Inativo"]["total_tasks"] == 0
    assert por_nome["Inativo"]["completion_rate"] == 0


def test_user_report_mantem_a_estrutura_original(
    client, app, seeded, member_headers
):
    with app.app_context():
        _populate(seeded)

    response = client.get(
        f"/reports/user/{seeded['member_id']}", headers=member_headers
    )

    assert response.status_code == 200
    body = response.get_json()
    assert set(body["user"]) == {"id", "name", "email"}
    assert body["statistics"] == {
        "total_tasks": 2,
        "done": 1,
        "pending": 1,
        "in_progress": 0,
        "cancelled": 0,
        "overdue": 0,
        # Prioridades 1 e 2 contam como alta.
        "high_priority": 2,
        "completion_rate": 50.0,
    }


def test_user_report_de_usuario_inexistente(client, member_headers):
    response = client.get("/reports/user/9999", headers=member_headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Usuário não encontrado"}
