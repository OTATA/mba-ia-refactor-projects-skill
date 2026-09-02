"""Notificações disparadas por eventos de pedido.

Mantém exatamente os avisos que o código original emitia com `print`, agora
através do `logging` e isolados em um colaborador, para que o controller não
precise conhecê-los.
"""

from __future__ import annotations

import logging

from ..models.pedido import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info(
            "Notificando criação do pedido %s do usuário %s (email, SMS e push)",
            pedido_id,
            usuario_id,
        )

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_APROVADO:
            logger.info("Pedido %s aprovado: preparar envio", pedido_id)
        elif novo_status == STATUS_CANCELADO:
            logger.info("Pedido %s cancelado: devolver estoque", pedido_id)
