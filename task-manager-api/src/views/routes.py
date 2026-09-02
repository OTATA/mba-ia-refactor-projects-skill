"""Roteamento e política de acesso.

Único lugar que mapeia URL + método para um controller. As 22 rotas são
exatamente as mesmas do original — mesmos paths, mesmos métodos — mas o
blueprint de categorias saiu de `report_routes.py`, onde não pertencia.

A política de autenticação está declarada aqui, junto das URLs, para que dê
para auditá-la de uma olhada:

| Rota                          | Acesso                          |
|-------------------------------|---------------------------------|
| `GET /`, `GET /health`        | público                         |
| `POST /login`                 | público                         |
| `POST /users`                 | público (registro)              |
| `DELETE /users/<id>`          | admin                           |
| `PUT /users/<id>`             | o próprio usuário ou admin      |
| todas as demais               | qualquer usuário autenticado    |

Duas regras adicionais são aplicadas no controller de usuários, porque
dependem do corpo da requisição:

- `role` e `active` em `PUT /users/<id>` só podem ser alterados por admin.
- `POST /users` só aceita um `role` diferente de `user` se quem chamou for
  admin autenticado.

Juntas, elas fecham a escalação de privilégio do original, em que qualquer
anônimo se tornava admin com um `PUT /users/<id>`.
"""

from __future__ import annotations

from flask import Blueprint

from ..controllers import (
    auth_controller,
    category_controller,
    report_controller,
    system_controller,
    task_controller,
    user_controller,
)
from ..middlewares.auth import optional_auth, require_auth, require_role
from ..models.enums import UserRole

tasks = Blueprint("tasks", __name__)
tasks.add_url_rule(
    "/tasks", "list", require_auth(task_controller.list_tasks), methods=["GET"]
)
# Registrada antes de `/tasks/<int:task_id>` por clareza; o conversor
# `int` já impediria a colisão com `/tasks/search` e `/tasks/stats`.
tasks.add_url_rule(
    "/tasks/search",
    "search",
    require_auth(task_controller.search_tasks),
    methods=["GET"],
)
tasks.add_url_rule(
    "/tasks/stats", "stats", require_auth(task_controller.task_stats), methods=["GET"]
)
tasks.add_url_rule(
    "/tasks/<int:task_id>",
    "get",
    require_auth(task_controller.get_task),
    methods=["GET"],
)
tasks.add_url_rule(
    "/tasks", "create", require_auth(task_controller.create_task), methods=["POST"]
)
tasks.add_url_rule(
    "/tasks/<int:task_id>",
    "update",
    require_auth(task_controller.update_task),
    methods=["PUT"],
)
tasks.add_url_rule(
    "/tasks/<int:task_id>",
    "delete",
    require_auth(task_controller.delete_task),
    methods=["DELETE"],
)

users = Blueprint("users", __name__)
users.add_url_rule(
    "/users", "list", require_auth(user_controller.list_users), methods=["GET"]
)
users.add_url_rule(
    "/users/<int:user_id>",
    "get",
    require_auth(user_controller.get_user),
    methods=["GET"],
)
users.add_url_rule(
    "/users", "create", optional_auth(user_controller.create_user), methods=["POST"]
)
users.add_url_rule(
    "/users/<int:user_id>",
    "update",
    require_auth(user_controller.update_user),
    methods=["PUT"],
)
users.add_url_rule(
    "/users/<int:user_id>",
    "delete",
    require_role(UserRole.ADMIN)(user_controller.delete_user),
    methods=["DELETE"],
)
users.add_url_rule(
    "/users/<int:user_id>/tasks",
    "tasks",
    require_auth(user_controller.list_user_tasks),
    methods=["GET"],
)

auth = Blueprint("auth", __name__)
auth.add_url_rule("/login", "login", auth_controller.login, methods=["POST"])

categories = Blueprint("categories", __name__)
categories.add_url_rule(
    "/categories",
    "list",
    require_auth(category_controller.list_categories),
    methods=["GET"],
)
categories.add_url_rule(
    "/categories",
    "create",
    require_auth(category_controller.create_category),
    methods=["POST"],
)
categories.add_url_rule(
    "/categories/<int:category_id>",
    "update",
    require_auth(category_controller.update_category),
    methods=["PUT"],
)
categories.add_url_rule(
    "/categories/<int:category_id>",
    "delete",
    require_auth(category_controller.delete_category),
    methods=["DELETE"],
)

reports = Blueprint("reports", __name__)
reports.add_url_rule(
    "/reports/summary",
    "summary",
    require_auth(report_controller.summary),
    methods=["GET"],
)
reports.add_url_rule(
    "/reports/user/<int:user_id>",
    "user",
    require_auth(report_controller.user_report),
    methods=["GET"],
)

system = Blueprint("system", __name__)
system.add_url_rule("/", "index", system_controller.index, methods=["GET"])
system.add_url_rule("/health", "health", system_controller.health, methods=["GET"])

BLUEPRINTS = (tasks, users, auth, categories, reports, system)


def register_routes(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
