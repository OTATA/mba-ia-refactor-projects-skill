"""Orquestração dos casos de uso de pedido.

A criação inteira roda em uma transação: se qualquer item falhar na baixa de
estoque, nada é persistido. No código original o pedido e parte dos itens
podiam ficar gravados.
"""

from __future__ import annotations

import logging

from ..exceptions import NaoEncontradoError, RegraDeNegocioError, ValidacaoError
from ..infrastructure.database import transaction
from ..models.pedido import (
    ItemPedido,
    STATUS_INICIAL,
    normalizar_itens_solicitados,
    validar_status,
)

logger = logging.getLogger(__name__)


class PedidoService:
    def __init__(self, pedido_repository, produto_repository, notificacao_service):
        self._pedidos = pedido_repository
        self._produtos = produto_repository
        self._notificacoes = notificacao_service

    def listar(self, usuario_id=None):
        return self._pedidos.listar(usuario_id)

    def criar(self, usuario_id, itens_payload):
        if not usuario_id:
            raise ValidacaoError("Usuario ID é obrigatório")

        itens_solicitados = normalizar_itens_solicitados(itens_payload)

        with transaction():
            catalogo = self._produtos.buscar_por_ids(
                item.produto_id for item in itens_solicitados
            )
            itens = self._precificar(itens_solicitados, catalogo)
            total = sum(item.subtotal for item in itens)

            pedido_id = self._pedidos.criar(usuario_id, STATUS_INICIAL, total)
            for item in itens:
                self._pedidos.adicionar_item(pedido_id, item)
                if not self._produtos.reduzir_estoque(item.produto_id, item.quantidade):
                    raise RegraDeNegocioError(
                        f"Estoque insuficiente para {item.produto_nome}"
                    )

        logger.info("Pedido %s criado com total %s", pedido_id, total)
        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    @staticmethod
    def _precificar(itens_solicitados, catalogo):
        """Confronta os itens pedidos com o catálogo, aplicando o preço vigente."""
        itens = []
        for solicitado in itens_solicitados:
            produto = catalogo.get(solicitado.produto_id)
            if produto is None:
                raise RegraDeNegocioError(
                    f"Produto {solicitado.produto_id} não encontrado"
                )
            if not produto.tem_estoque_para(solicitado.quantidade):
                raise RegraDeNegocioError(f"Estoque insuficiente para {produto.nome}")

            itens.append(
                ItemPedido(
                    produto_id=produto.id,
                    quantidade=solicitado.quantidade,
                    preco_unitario=produto.preco,
                    produto_nome=produto.nome,
                )
            )
        return itens

    def atualizar_status(self, pedido_id, novo_status):
        status = validar_status(novo_status)

        with transaction():
            if not self._pedidos.atualizar_status(pedido_id, status):
                raise NaoEncontradoError("Pedido não encontrado")

        logger.info("Pedido %s alterado para o status %s", pedido_id, status)
        self._notificacoes.status_alterado(pedido_id, status)
