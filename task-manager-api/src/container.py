"""Composição das dependências que precisam de configuração em runtime.

Services e repositories deste projeto são módulos com funções — não têm
estado e por isso não precisam de fábrica. `NotificationService` é a exceção:
depende das credenciais SMTP, que vêm da configuração da aplicação.
"""

from __future__ import annotations

from flask import current_app

from .services.notification_service import NotificationService


def notification_service():
    return NotificationService(current_app.config["SMTP"])
