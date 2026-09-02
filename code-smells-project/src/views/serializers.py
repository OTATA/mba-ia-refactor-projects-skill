"""Representação externa das entidades (camada View).

Cada serializer define explicitamente o contrato do endpoint. É o que impede
que campos internos — notadamente o hash da senha — vazem por serialização
automática da entidade de persistência.
"""

from __future__ import annotations

from ..models.relatorio import CASAS_DECIMAIS


def serializar_produto(produto):
    return {
        "id": produto.id,
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco": produto.preco,
        "estoque": produto.estoque,
        "categoria": produto.categoria,
        "ativo": produto.ativo,
        "criado_em": produto.criado_em,
    }


def serializar_usuario(usuario):
    """Representação pública do usuário. O hash da senha não é exposto."""
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo,
        "criado_em": usuario.criado_em,
    }


def serializar_usuario_autenticado(usuario):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo,
    }


def serializar_item_pedido(item):
    return {
        "produto_id": item.produto_id,
        "produto_nome": item.produto_nome,
        "quantidade": item.quantidade,
        "preco_unitario": item.preco_unitario,
    }


def serializar_pedido(pedido):
    return {
        "id": pedido.id,
        "usuario_id": pedido.usuario_id,
        "status": pedido.status,
        "total": pedido.total,
        "criado_em": pedido.criado_em,
        "itens": [serializar_item_pedido(item) for item in pedido.itens],
    }


def serializar_relatorio_vendas(relatorio):
    return {
        "total_pedidos": relatorio.total_pedidos,
        "faturamento_bruto": round(relatorio.faturamento_bruto, CASAS_DECIMAIS),
        "desconto_aplicavel": round(relatorio.desconto_aplicavel, CASAS_DECIMAIS),
        "faturamento_liquido": round(relatorio.faturamento_liquido, CASAS_DECIMAIS),
        "pedidos_pendentes": relatorio.pedidos_pendentes,
        "pedidos_aprovados": relatorio.pedidos_aprovados,
        "pedidos_cancelados": relatorio.pedidos_cancelados,
        "ticket_medio": round(relatorio.ticket_medio, CASAS_DECIMAIS),
    }


def serializar_colecao(itens, serializer):
    return [serializer(item) for item in itens]
