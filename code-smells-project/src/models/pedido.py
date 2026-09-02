"""Domínio de Pedido: entidade, itens e transições de status."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..exceptions import ValidacaoError

STATUS_INICIAL = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_INICIAL, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

QUANTIDADE_MINIMA_ITEM = 1
ITENS_MINIMOS_POR_PEDIDO = 1

PRODUTO_DESCONHECIDO = "Desconhecido"


@dataclass(frozen=True)
class ItemSolicitado:
    """Item pedido pelo cliente, antes de ser confrontado com o catálogo."""

    produto_id: int
    quantidade: int


@dataclass(frozen=True)
class ItemPedido:
    """Item já precificado, como fica registrado no pedido."""

    produto_id: int
    quantidade: int
    preco_unitario: float
    produto_nome: str = PRODUTO_DESCONHECIDO

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade


@dataclass(frozen=True)
class Pedido:
    usuario_id: int
    status: str
    total: float
    id: int = None
    criado_em: str = None
    itens: tuple = field(default_factory=tuple)


def validar_status(status):
    if status not in STATUS_VALIDOS:
        raise ValidacaoError("Status inválido")
    return status


def normalizar_itens_solicitados(payload):
    """Valida a lista de itens da requisição e a converte em `ItemSolicitado`.

    No código original chaves ausentes viravam `KeyError` (HTTP 500) e
    quantidades não positivas passavam direto, creditando estoque e gerando
    total negativo. Ambos os casos agora são recusados na borda do domínio.
    """
    if not payload or len(payload) < ITENS_MINIMOS_POR_PEDIDO:
        raise ValidacaoError("Pedido deve ter pelo menos 1 item")

    itens = []
    for bruto in payload:
        if not isinstance(bruto, dict):
            raise ValidacaoError("Item do pedido deve ser um objeto")
        if "produto_id" not in bruto or "quantidade" not in bruto:
            raise ValidacaoError("Item do pedido deve informar produto_id e quantidade")

        try:
            produto_id = int(bruto["produto_id"])
            quantidade = int(bruto["quantidade"])
        except (TypeError, ValueError):
            raise ValidacaoError("produto_id e quantidade devem ser números inteiros")

        if quantidade < QUANTIDADE_MINIMA_ITEM:
            raise ValidacaoError("Quantidade do item deve ser maior que zero")

        itens.append(ItemSolicitado(produto_id=produto_id, quantidade=quantidade))

    return itens
