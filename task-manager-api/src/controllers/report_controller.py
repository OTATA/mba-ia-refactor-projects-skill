"""Controller de relatórios.

O cálculo dos números está em `services/report_service.py`; aqui só sobrou a
delegação. No original, `summary_report` tinha 90 linhas de queries e loops
dentro do próprio handler.
"""

from __future__ import annotations

from ..services import report_service, user_service
from ..views import responses


def summary():
    return responses.ok(report_service.summary())


def user_report(user_id):
    user = user_service.get(user_id)
    return responses.ok(report_service.for_user(user))
