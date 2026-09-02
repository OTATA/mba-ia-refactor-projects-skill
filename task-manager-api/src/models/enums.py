"""Vocabulário do domínio: status, papéis e limites das entidades.

No código original estes valores eram literais repetidos em até cinco
arquivos (`routes/task_routes.py`, `routes/user_routes.py`, `models/task.py`,
`utils/helpers.py`), enquanto as constantes equivalentes em
`utils/helpers.py:110-116` existiam sem nunca serem usadas.

Os valores são idênticos aos originais — inclusive `MIN_PASSWORD_LENGTH = 4`,
que é fraco e está registrado no relatório de auditoria, mas alterá-lo mudaria
uma regra de negócio e invalidaria as senhas existentes.
"""

from __future__ import annotations

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def values(cls):
        return tuple(status.value for status in cls)

    @classmethod
    def is_valid(cls, value):
        return value in cls.values()


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"

    @classmethod
    def values(cls):
        return tuple(role.value for role in cls)

    @classmethod
    def is_valid(cls, value):
        return value in cls.values()


#: Status em que uma task deixa de poder estar atrasada.
CLOSED_STATUSES = frozenset({TaskStatus.DONE.value, TaskStatus.CANCELLED.value})

DEFAULT_STATUS = TaskStatus.PENDING.value
DEFAULT_ROLE = UserRole.USER.value

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3

#: Prioridades 1 e 2 contam como "alta" nos relatórios.
HIGH_PRIORITY_THRESHOLD = 2

MIN_PASSWORD_LENGTH = 4

DEFAULT_COLOR = "#000000"

#: Formato aceito em `due_date`, igual ao original.
DUE_DATE_FORMAT = "%Y-%m-%d"

#: Rótulos das prioridades no relatório `/reports/summary`.
PRIORITY_LABELS = {
    1: "critical",
    2: "high",
    3: "medium",
    4: "low",
    5: "minimal",
}
