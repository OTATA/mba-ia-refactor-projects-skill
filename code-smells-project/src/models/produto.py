"""Domínio de Produto: entidade e invariantes.

As regras aqui são as mesmas do código original; a diferença é que passam a
viver em um único lugar, aplicado tanto na criação quanto na atualização.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..exceptions import ValidacaoError

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200
PRECO_MINIMO = 0
ESTOQUE_MINIMO = 0


@dataclass(frozen=True)
class Produto:
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str
    id: int = None
    ativo: int = 1
    criado_em: str = None

    def __post_init__(self):
        self._validar()

    def _validar(self):
        # A ordem reproduz a sequência de mensagens da API original.
        if self.preco < PRECO_MINIMO:
            raise ValidacaoError("Preço não pode ser negativo")
        if self.estoque < ESTOQUE_MINIMO:
            raise ValidacaoError("Estoque não pode ser negativo")
        if len(self.nome) < NOME_TAMANHO_MINIMO:
            raise ValidacaoError("Nome muito curto")
        if len(self.nome) > NOME_TAMANHO_MAXIMO:
            raise ValidacaoError("Nome muito longo")
        if self.categoria not in CATEGORIAS_VALIDAS:
            raise ValidacaoError(
                f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}"
            )

    def com_dados(self, **alteracoes):
        """Retorna uma nova instância validada com os campos alterados."""
        return replace(self, **alteracoes)

    def tem_estoque_para(self, quantidade):
        return self.estoque >= quantidade
