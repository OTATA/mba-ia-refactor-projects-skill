"""Fronteira transacional explícita.

No original, cada rota chamava `db.session.commit()` dentro do próprio
`try/except:` e fazia `rollback()` no bloco nu. Em `delete_user`
(`routes/user_routes.py:140-151`) as tasks eram marcadas para deleção *fora*
do `try`, e a atomicidade só funcionava por acidente.

Aqui a unidade de trabalho é um context manager: comita no fim do bloco,
faz rollback em qualquer exceção e deixa a exceção subir para o error
handler, que decide o status HTTP e loga o stack trace.
"""

from __future__ import annotations

from contextlib import contextmanager

from ..extensions import db


@contextmanager
def commit_on_success():
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
