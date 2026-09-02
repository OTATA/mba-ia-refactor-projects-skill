"""Composição das dependências por requisição.

Repositórios recebem a conexão do contexto atual, então os serviços são
montados por requisição. Os controllers pedem o serviço aqui e não conhecem
repositório, conexão nem SQL.
"""

from __future__ import annotations

from .infrastructure.database import get_connection
from .repositories.pedido_repository import PedidoRepository
from .repositories.produto_repository import ProdutoRepository
from .repositories.usuario_repository import UsuarioRepository
from .services.health_service import HealthService
from .services.notificacao_service import NotificacaoService
from .services.pedido_service import PedidoService
from .services.produto_service import ProdutoService
from .services.relatorio_service import RelatorioService
from .services.usuario_service import UsuarioService


def _produto_repository():
    return ProdutoRepository(get_connection())


def _usuario_repository():
    return UsuarioRepository(get_connection())


def _pedido_repository():
    return PedidoRepository(get_connection())


def produto_service():
    return ProdutoService(_produto_repository())


def usuario_service():
    return UsuarioService(_usuario_repository())


def pedido_service():
    return PedidoService(
        _pedido_repository(), _produto_repository(), NotificacaoService()
    )


def relatorio_service():
    return RelatorioService(_pedido_repository())


def health_service():
    return HealthService(
        _produto_repository(), _usuario_repository(), _pedido_repository()
    )
