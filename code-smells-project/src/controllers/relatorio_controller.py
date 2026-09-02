"""Controller de relatórios."""

from __future__ import annotations

from ..container import relatorio_service
from ..views.responses import resposta_sucesso
from ..views.serializers import serializar_relatorio_vendas


def vendas():
    relatorio = relatorio_service().vendas()
    return resposta_sucesso(serializar_relatorio_vendas(relatorio))
