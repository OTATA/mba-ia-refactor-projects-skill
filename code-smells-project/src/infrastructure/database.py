"""Gerenciamento de conexão SQLite.

Uma conexão por contexto de aplicação (requisição), armazenada em `flask.g` e
fechada no teardown. Substitui a conexão global compartilhada entre threads.

A conexão roda em autocommit (`isolation_level=None`); escritas que precisam de
atomicidade devem usar o context manager `transaction()`.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from flask import current_app, g

_CONNECTION_KEY = "_db_connection"


def connect(database_path):
    connection = sqlite3.connect(database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection


def get_connection():
    connection = g.get(_CONNECTION_KEY)
    if connection is None:
        connection = connect(current_app.config["DATABASE_PATH"])
        setattr(g, _CONNECTION_KEY, connection)
    return connection


def close_connection(_exception=None):
    connection = g.pop(_CONNECTION_KEY, None)
    if connection is not None:
        connection.close()


@contextmanager
def transaction():
    """Transação explícita com rollback em qualquer falha.

    `BEGIN IMMEDIATE` adquire o lock de escrita na abertura, serializando
    escritas concorrentes em vez de descobrir o conflito no commit.
    """
    connection = get_connection()
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.rollback()
        raise
    connection.commit()
