"""Roteamento: único lugar que mapeia URL + método para um controller.

Os endpoints e os métodos são exatamente os do `app.py` original, exceto as
rotas administrativas `POST /admin/reset-db` e `POST /admin/query`, removidas
por permitirem destruição de dados e execução de SQL arbitrário sem
autenticação.
"""

from __future__ import annotations

from flask import Blueprint

from ..controllers import (
    health_controller,
    pedido_controller,
    produto_controller,
    relatorio_controller,
    usuario_controller,
)

produtos = Blueprint("produtos", __name__)
produtos.add_url_rule("/produtos", "listar", produto_controller.listar, methods=["GET"])
produtos.add_url_rule(
    "/produtos/busca", "pesquisar", produto_controller.pesquisar, methods=["GET"]
)
produtos.add_url_rule(
    "/produtos/<int:produto_id>", "buscar", produto_controller.buscar, methods=["GET"]
)
produtos.add_url_rule("/produtos", "criar", produto_controller.criar, methods=["POST"])
produtos.add_url_rule(
    "/produtos/<int:produto_id>",
    "atualizar",
    produto_controller.atualizar,
    methods=["PUT"],
)
produtos.add_url_rule(
    "/produtos/<int:produto_id>",
    "deletar",
    produto_controller.deletar,
    methods=["DELETE"],
)

usuarios = Blueprint("usuarios", __name__)
usuarios.add_url_rule("/usuarios", "listar", usuario_controller.listar, methods=["GET"])
usuarios.add_url_rule(
    "/usuarios/<int:usuario_id>", "buscar", usuario_controller.buscar, methods=["GET"]
)
usuarios.add_url_rule("/usuarios", "criar", usuario_controller.criar, methods=["POST"])
usuarios.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

pedidos = Blueprint("pedidos", __name__)
pedidos.add_url_rule("/pedidos", "criar", pedido_controller.criar, methods=["POST"])
pedidos.add_url_rule(
    "/pedidos", "listar_todos", pedido_controller.listar_todos, methods=["GET"]
)
pedidos.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_por_usuario",
    pedido_controller.listar_por_usuario,
    methods=["GET"],
)
pedidos.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status",
    pedido_controller.atualizar_status,
    methods=["PUT"],
)

relatorios = Blueprint("relatorios", __name__)
relatorios.add_url_rule(
    "/relatorios/vendas", "vendas", relatorio_controller.vendas, methods=["GET"]
)

sistema = Blueprint("sistema", __name__)
sistema.add_url_rule("/", "index", health_controller.index, methods=["GET"])
sistema.add_url_rule("/health", "health", health_controller.health, methods=["GET"])

BLUEPRINTS = (produtos, usuarios, pedidos, relatorios, sistema)


def registrar_rotas(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
