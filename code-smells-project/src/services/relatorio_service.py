"""Caso de uso do relatório de vendas."""

from __future__ import annotations

from ..models.relatorio import RelatorioVendas


class RelatorioService:
    def __init__(self, pedido_repository):
        self._pedidos = pedido_repository

    def vendas(self):
        return RelatorioVendas.a_partir_do_resumo(self._pedidos.resumo_vendas())
