"""Verificação de liveness da aplicação e do banco."""

from __future__ import annotations


class HealthService:
    def __init__(self, produto_repository, usuario_repository, pedido_repository):
        self._produtos = produto_repository
        self._usuarios = usuario_repository
        self._pedidos = pedido_repository

    def contagens(self):
        return {
            "produtos": self._produtos.contar(),
            "usuarios": self._usuarios.contar(),
            "pedidos": self._pedidos.contar(),
        }
