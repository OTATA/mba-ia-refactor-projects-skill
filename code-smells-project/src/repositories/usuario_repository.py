"""Acesso a dados de usuários. Todo SQL usa parâmetros vinculados."""

from __future__ import annotations

from ..models.usuario import Usuario

_COLUNAS = "id, nome, email, senha, tipo, criado_em"


def _para_usuario(row):
    return Usuario(
        id=row["id"],
        nome=row["nome"],
        email=row["email"],
        senha_hash=row["senha"],
        tipo=row["tipo"],
        criado_em=row["criado_em"],
    )


class UsuarioRepository:
    def __init__(self, connection):
        self._connection = connection

    def listar(self):
        rows = self._connection.execute(f"SELECT {_COLUNAS} FROM usuarios").fetchall()
        return [_para_usuario(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._connection.execute(
            f"SELECT {_COLUNAS} FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _para_usuario(row) if row else None

    def buscar_por_email(self, email):
        row = self._connection.execute(
            f"SELECT {_COLUNAS} FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return _para_usuario(row) if row else None

    def criar(self, usuario):
        cursor = self._connection.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (usuario.nome, usuario.email, usuario.senha_hash, usuario.tipo),
        )
        return cursor.lastrowid

    def contar(self):
        return self._connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
