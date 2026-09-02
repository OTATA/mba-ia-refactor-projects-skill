"""Acesso a dados de produtos. Todo SQL usa parâmetros vinculados."""

from __future__ import annotations

from ..models.produto import Produto

_COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def _para_produto(row):
    return Produto(
        id=row["id"],
        nome=row["nome"],
        descricao=row["descricao"],
        preco=row["preco"],
        estoque=row["estoque"],
        categoria=row["categoria"],
        ativo=row["ativo"],
        criado_em=row["criado_em"],
    )


class ProdutoRepository:
    def __init__(self, connection):
        self._connection = connection

    def listar(self):
        rows = self._connection.execute(f"SELECT {_COLUNAS} FROM produtos").fetchall()
        return [_para_produto(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._connection.execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _para_produto(row) if row else None

    def buscar_por_ids(self, produto_ids):
        """Carrega vários produtos em uma única query, indexados por id."""
        ids = tuple(dict.fromkeys(produto_ids))
        if not ids:
            return {}

        placeholders = ", ".join("?" for _ in ids)
        rows = self._connection.execute(
            f"SELECT {_COLUNAS} FROM produtos WHERE id IN ({placeholders})", ids
        ).fetchall()
        return {row["id"]: _para_produto(row) for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        sql = [f"SELECT {_COLUNAS} FROM produtos WHERE 1=1"]
        parametros = []

        if termo:
            sql.append("AND (nome LIKE ? OR descricao LIKE ?)")
            parametros.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            sql.append("AND categoria = ?")
            parametros.append(categoria)
        if preco_min:
            sql.append("AND preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            sql.append("AND preco <= ?")
            parametros.append(preco_max)

        rows = self._connection.execute(" ".join(sql), parametros).fetchall()
        return [_para_produto(row) for row in rows]

    def criar(self, produto):
        cursor = self._connection.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                produto.nome,
                produto.descricao,
                produto.preco,
                produto.estoque,
                produto.categoria,
            ),
        )
        return cursor.lastrowid

    def atualizar(self, produto_id, produto):
        cursor = self._connection.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (
                produto.nome,
                produto.descricao,
                produto.preco,
                produto.estoque,
                produto.categoria,
                produto_id,
            ),
        )
        return cursor.rowcount > 0

    def deletar(self, produto_id):
        cursor = self._connection.execute(
            "DELETE FROM produtos WHERE id = ?", (produto_id,)
        )
        return cursor.rowcount > 0

    def reduzir_estoque(self, produto_id, quantidade):
        """Baixa condicional de estoque.

        A condição `estoque >= ?` fecha a corrida entre a verificação e a
        escrita: se outra transação consumiu o saldo antes, `rowcount` é 0 e o
        chamador aborta a operação.
        """
        cursor = self._connection.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount > 0

    def contar(self):
        return self._connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
