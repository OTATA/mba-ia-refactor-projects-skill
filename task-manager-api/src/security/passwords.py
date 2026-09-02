"""Hash de senhas.

Substitui `hashlib.md5(pwd.encode()).hexdigest()` de `models/user.py:29`.
MD5 é um hash rápido de propósito geral, sem salt e com colisões conhecidas
desde 2004 — inadequado para senhas. `generate_password_hash` do Werkzeug usa
scrypt com salt aleatório por senha e fator de custo, e a verificação é de
tempo constante, fechando também o timing attack do `==` original.

Migração: os hashes MD5 gravados no banco não são conversíveis. É preciso
rodar `python seed.py` novamente (ou fazer os usuários redefinirem a senha).
"""

from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

#: scrypt é o default do Werkzeug 3.x; explícito para não depender do default.
HASH_METHOD = "scrypt"


def hash_password(raw_password):
    return generate_password_hash(raw_password, method=HASH_METHOD)


def verify_password(stored_hash, raw_password):
    """Compara em tempo constante. Nunca levanta para hash malformado."""
    if not stored_hash or raw_password is None:
        return False
    try:
        return check_password_hash(stored_hash, raw_password)
    except ValueError:
        # Hash em formato desconhecido (ex.: MD5 legado). Trata como não
        # conferindo, em vez de derrubar a requisição com HTTP 500.
        return False
