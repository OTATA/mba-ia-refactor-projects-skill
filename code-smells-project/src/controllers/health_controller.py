"""Controller de health check e index.

O health check devolve apenas liveness e contagens. A configuração da
aplicação — inclusive `SECRET_KEY`, que o código original expunha aqui — não
faz parte da resposta.
"""

from __future__ import annotations

from flask import jsonify

from ..config.settings import APP_VERSION
from ..container import health_service


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def health():
    contagens = health_service().contagens()
    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": APP_VERSION,
        }
    )
