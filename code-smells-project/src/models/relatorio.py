"""Regras de faturamento do relatório de vendas.

As faixas de desconto e o arredondamento são exatamente os do código original;
os limites deixam de ser números soltos dentro de uma cadeia de `elif`.
"""

from __future__ import annotations

from dataclasses import dataclass

CASAS_DECIMAIS = 2

# (faturamento mínimo exclusivo, percentual de desconto)
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)


def calcular_desconto(faturamento):
    for faturamento_minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return faturamento * percentual
    return 0


def calcular_ticket_medio(faturamento, total_pedidos):
    if total_pedidos <= 0:
        return 0
    return faturamento / total_pedidos


@dataclass(frozen=True)
class RelatorioVendas:
    total_pedidos: int
    faturamento_bruto: float
    pedidos_pendentes: int
    pedidos_aprovados: int
    pedidos_cancelados: int

    @classmethod
    def a_partir_do_resumo(cls, resumo):
        return cls(
            total_pedidos=resumo["total_pedidos"],
            faturamento_bruto=resumo["faturamento"],
            pedidos_pendentes=resumo["pendentes"],
            pedidos_aprovados=resumo["aprovados"],
            pedidos_cancelados=resumo["cancelados"],
        )

    @property
    def desconto_aplicavel(self):
        return calcular_desconto(self.faturamento_bruto)

    @property
    def faturamento_liquido(self):
        return self.faturamento_bruto - self.desconto_aplicavel

    @property
    def ticket_medio(self):
        return calcular_ticket_medio(self.faturamento_bruto, self.total_pedidos)
