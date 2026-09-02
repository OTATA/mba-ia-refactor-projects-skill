"""Acesso a dados de pedidos. Todo SQL usa parâmetros vinculados."""

from __future__ import annotations

from ..models.pedido import ItemPedido, Pedido, PRODUTO_DESCONHECIDO

# Uma única query resolve pedidos, itens e nome do produto. Substitui o padrão
# 1 + N + N*M de queries das listagens originais.
_SQL_LISTAGEM = """
    SELECT
        p.id            AS pedido_id,
        p.usuario_id    AS usuario_id,
        p.status        AS status,
        p.total         AS total,
        p.criado_em     AS criado_em,
        i.produto_id    AS produto_id,
        i.quantidade    AS quantidade,
        i.preco_unitario AS preco_unitario,
        pr.nome         AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    {filtro}
    ORDER BY p.id, i.id
"""


class PedidoRepository:
    def __init__(self, connection):
        self._connection = connection

    def listar(self, usuario_id=None):
        if usuario_id is None:
            sql = _SQL_LISTAGEM.format(filtro="")
            parametros = ()
        else:
            sql = _SQL_LISTAGEM.format(filtro="WHERE p.usuario_id = ?")
            parametros = (usuario_id,)

        return self._agrupar(self._connection.execute(sql, parametros).fetchall())

    @staticmethod
    def _agrupar(rows):
        pedidos = {}
        itens_por_pedido = {}

        for row in rows:
            pedido_id = row["pedido_id"]
            if pedido_id not in pedidos:
                pedidos[pedido_id] = {
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                }
                itens_por_pedido[pedido_id] = []

            if row["produto_id"] is None:
                continue

            itens_por_pedido[pedido_id].append(
                ItemPedido(
                    produto_id=row["produto_id"],
                    quantidade=row["quantidade"],
                    preco_unitario=row["preco_unitario"],
                    produto_nome=row["produto_nome"] or PRODUTO_DESCONHECIDO,
                )
            )

        return [
            Pedido(
                id=pedido_id,
                usuario_id=dados["usuario_id"],
                status=dados["status"],
                total=dados["total"],
                criado_em=dados["criado_em"],
                itens=tuple(itens_por_pedido[pedido_id]),
            )
            for pedido_id, dados in pedidos.items()
        ]

    def criar(self, usuario_id, status, total):
        cursor = self._connection.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, status, total),
        )
        return cursor.lastrowid

    def adicionar_item(self, pedido_id, item):
        self._connection.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, item.produto_id, item.quantidade, item.preco_unitario),
        )

    def atualizar_status(self, pedido_id, status):
        cursor = self._connection.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id)
        )
        return cursor.rowcount > 0

    def contar(self):
        return self._connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def resumo_vendas(self):
        """Agrega o relatório em uma query, no lugar das cinco originais."""
        row = self._connection.execute(
            """
            SELECT
                COUNT(*) AS total_pedidos,
                COALESCE(SUM(total), 0) AS faturamento,
                COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
                COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
                COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """
        ).fetchone()

        return {
            "total_pedidos": row["total_pedidos"],
            "faturamento": row["faturamento"],
            "pendentes": row["pendentes"],
            "aprovados": row["aprovados"],
            "cancelados": row["cancelados"],
        }
