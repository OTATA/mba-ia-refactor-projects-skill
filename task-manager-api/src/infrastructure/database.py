"""Criação do schema e enforcement de integridade referencial.

Duas correções em relação ao original:

- `db.create_all()` rodava como efeito colateral do import de `app.py`
  (`app.py:30-31`): importar o módulo — num teste, num script — já criava
  arquivos. Agora é uma função chamada explicitamente pelo composition root
  e condicionada por configuração.
- O SQLite ignora `FOREIGN KEY` a menos que `PRAGMA foreign_keys` esteja
  ligado. Sem isso, os `ON DELETE CASCADE`/`SET NULL` declarados nos models
  não teriam efeito nenhum.

`create_all()` só cria tabelas ausentes: nunca altera colunas existentes.
Para evoluir o schema, o passo seguinte é adotar Alembic/Flask-Migrate.
"""

from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..extensions import db

logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Liga a checagem de FK no SQLite, que vem desligada por padrão."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_schema(app):
    """Cria as tabelas ausentes. Idempotente."""
    with app.app_context():
        db.create_all()
    logger.info("Schema verificado")
