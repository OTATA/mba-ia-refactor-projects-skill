"""Validação de forma da requisição de produto.

Responsabilidade limitada ao nível de requisição: presença de campos e tipos.
Os limites de negócio (faixa de preço, tamanho de nome, categoria válida) são
invariantes da entidade `Produto` e são aplicados lá.
"""

from __future__ import annotations

from ..exceptions import ValidacaoError
from ..models.produto import CATEGORIA_PADRAO

CAMPOS_OBRIGATORIOS = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _exigir_numero(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidacaoError(mensagem)
    return valor


def _exigir_inteiro(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidacaoError(mensagem)
    return valor


def _exigir_texto(valor, mensagem):
    if not isinstance(valor, str):
        raise ValidacaoError(mensagem)
    return valor


def validar_payload_produto(dados):
    """Normaliza o corpo da requisição em kwargs para `Produto`."""
    for campo, mensagem in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            raise ValidacaoError(mensagem)

    return {
        "nome": _exigir_texto(dados["nome"], "Nome deve ser um texto"),
        "descricao": _exigir_texto(
            dados.get("descricao", ""), "Descrição deve ser um texto"
        ),
        "preco": _exigir_numero(dados["preco"], "Preço deve ser um número"),
        "estoque": _exigir_inteiro(
            dados["estoque"], "Estoque deve ser um número inteiro"
        ),
        "categoria": _exigir_texto(
            dados.get("categoria", CATEGORIA_PADRAO), "Categoria deve ser um texto"
        ),
    }
