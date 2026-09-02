"""Extensões do Flask instanciadas sem aplicação.

O `db` fica isolado num módulo próprio para que models, repositories e o
composition root possam importá-lo sem ciclo. Equivale ao `database.py`
original, agora dentro de `src/`.
"""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
