"""Controller das rotas de sistema (`/` e `/health`).

No original estas duas rotas estavam declaradas direto no `app.py`, junto da
configuração e do `db.create_all()`.
"""

from __future__ import annotations

from ..config.settings import APP_NAME, APP_VERSION
from ..infrastructure.clock import utcnow
from ..views import responses


def index():
    return responses.ok({"message": APP_NAME, "version": APP_VERSION})


def health():
    return responses.ok({"status": "ok", "timestamp": str(utcnow())})
