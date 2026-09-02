"""Entidade User.

Mudanças em relação a `models/user.py`:

- `to_dict()` saiu — e com ele o vazamento do campo `password`, que o método
  original incluía e que era devolvido por `GET /users/<id>`, `POST /users`,
  `PUT /users/<id>` e `POST /login`.
- O hash MD5 sem salt foi substituído por um KDF com salt e fator de custo
  (`src/security/passwords.py`), e a comparação passou a ser de tempo
  constante. MD5 é rápido por natureza: hashes de senhas curtas caem em
  segundos por rainbow table.
- `assign_role` protege a invariante em vez de deixar a rota atribuir o campo
  livremente.
"""

from __future__ import annotations

from ..exceptions import ValidationError
from ..extensions import db
from ..infrastructure.clock import utcnow
from ..security.passwords import hash_password, verify_password
from .enums import DEFAULT_ROLE, UserRole

MESSAGE_INVALID_ROLE = "Role inválido"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # `passive_deletes` deixa a remoção em cascata para o banco, em vez do
    # loop de DELETEs que `delete_user` fazia à mão no original.
    tasks = db.relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, raw_password):
        self.password = hash_password(raw_password)

    def check_password(self, raw_password):
        return verify_password(self.password, raw_password)

    def assign_role(self, role):
        if not UserRole.is_valid(role):
            raise ValidationError(MESSAGE_INVALID_ROLE)
        self.role = role

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN.value
