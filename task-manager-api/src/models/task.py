"""Entidade Task e suas invariantes de domínio.

Mudanças em relação a `models/task.py`:

- `to_dict()` saiu. Decidir o formato da resposta é responsabilidade da View
  (`src/views/serializers.py`); o model não conhece apresentação.
- `is_overdue()` deixa de ser código morto e passa a ser a *única* definição
  de "atrasada". A regra estava reescrita à mão em sete lugares do original.
- `assign_status`/`assign_priority` protegem as invariantes em vez de deixar
  as rotas atribuírem os campos diretamente sem validar.
"""

from __future__ import annotations

from ..exceptions import ValidationError
from ..extensions import db
from ..infrastructure.clock import utcnow
from .enums import (
    CLOSED_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TaskStatus,
)

TAG_SEPARATOR = ","

MESSAGE_INVALID_STATUS = "Status inválido"
MESSAGE_INVALID_PRIORITY = "Prioridade deve ser entre 1 e 5"


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    # Integridade referencial declarada no schema, não reimplementada na
    # aplicação: o original apagava as tasks do usuário num loop manual e
    # deixava FKs órfãs ao apagar uma categoria.
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", back_populates="tasks")
    category = db.relationship("Category", back_populates="tasks")

    def is_overdue(self, now=None):
        """Vencida e ainda aberta. Definição canônica de "atrasada"."""
        if not self.due_date:
            return False
        reference = utcnow() if now is None else now
        return self.due_date < reference and self.status not in CLOSED_STATUSES

    def days_overdue(self, now=None):
        """Dias de atraso, ou 0 se a task não está atrasada."""
        if not self.is_overdue(now):
            return 0
        reference = utcnow() if now is None else now
        return (reference - self.due_date).days

    @property
    def tag_list(self):
        """Tags como lista. O schema guarda uma string separada por vírgula."""
        if not self.tags:
            return []
        return self.tags.split(TAG_SEPARATOR)

    def assign_status(self, status):
        if not TaskStatus.is_valid(status):
            raise ValidationError(MESSAGE_INVALID_STATUS)
        self.status = status

    def assign_priority(self, priority):
        if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
            raise ValidationError(MESSAGE_INVALID_PRIORITY)
        self.priority = priority
