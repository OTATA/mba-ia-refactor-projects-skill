"""Fonte única do "agora" da aplicação.

`datetime.utcnow()` está depreciada desde o Python 3.12 e aparecia 18 vezes no
código original. O substituto recomendado, `datetime.now(UTC)`, devolve um
datetime *aware* — mas as colunas do schema são `db.DateTime` sem
`timezone=True`, então o banco guarda datetimes *naive*. Comparar aware com
naive levanta `TypeError`, o que quebraria `is_overdue` e todos os relatórios.

Esta função usa a API atual e normaliza para naive-UTC, preservando exatamente
a semântica anterior. Migrar o schema para `DateTime(timezone=True)` é o passo
seguinte e envolve migration de dados; até lá, todo o código passa por aqui.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow():
    """Instante atual em UTC, sem tzinfo (compatível com o schema atual)."""
    return datetime.now(UTC).replace(tzinfo=None)
