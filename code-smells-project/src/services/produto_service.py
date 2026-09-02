"""Orquestração dos casos de uso de produto."""

from __future__ import annotations

import logging

from ..exceptions import NaoEncontradoError
from ..infrastructure.database import transaction
from ..models.produto import Produto

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, produto_repository):
        self._produtos = produto_repository

    def listar(self):
        produtos = self._produtos.listar()
        logger.info("Listando %s produtos", len(produtos))
        return produtos

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NaoEncontradoError("Produto não encontrado")
        return produto

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        return self._produtos.pesquisar(termo, categoria, preco_min, preco_max)

    def criar(self, dados_validados):
        produto = Produto(**dados_validados)
        with transaction():
            produto_id = self._produtos.criar(produto)
        logger.info("Produto criado com id %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados_validados):
        produto = Produto(**dados_validados)
        with transaction():
            if self._produtos.buscar_por_id(produto_id) is None:
                raise NaoEncontradoError("Produto não encontrado")
            self._produtos.atualizar(produto_id, produto)
        logger.info("Produto %s atualizado", produto_id)

    def deletar(self, produto_id):
        with transaction():
            if not self._produtos.deletar(produto_id):
                raise NaoEncontradoError("Produto não encontrado")
        logger.info("Produto %s deletado", produto_id)
