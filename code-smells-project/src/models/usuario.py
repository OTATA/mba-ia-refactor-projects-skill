"""Domínio de Usuário.

A senha nunca circula em texto puro fora do momento do cadastro/autenticação:
a entidade carrega apenas o hash, e a verificação acontece em memória.
"""

from __future__ import annotations

from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"


@dataclass(frozen=True)
class Usuario:
    nome: str
    email: str
    senha_hash: str
    tipo: str = TIPO_PADRAO
    id: int = None
    criado_em: str = None

    @classmethod
    def novo(cls, nome, email, senha, tipo=TIPO_PADRAO):
        return cls(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
            tipo=tipo,
        )

    def senha_confere(self, senha):
        if not self.senha_hash:
            return False
        return check_password_hash(self.senha_hash, senha)
