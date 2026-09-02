"""Script para popular o banco com dados iniciais.

Os dados são os mesmos do original: 3 usuários, 4 categorias e 10 tasks.

Atenção: as senhas passaram a ser gravadas com scrypt em vez de MD5, e os
hashes antigos não são conversíveis. Rode este script novamente após a
refatoração — o login com o banco antigo vai falhar.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from src.app import create_app
from src.extensions import db
from src.infrastructure.clock import utcnow
from src.models.category import Category
from src.models.task import Task
from src.models.user import User

logger = logging.getLogger(__name__)

USERS = (
    {"name": "João Silva", "email": "joao@email.com", "password": "1234", "role": "admin"},
    {"name": "Maria Santos", "email": "maria@email.com", "password": "abcd", "role": "user"},
    {"name": "Pedro Oliveira", "email": "pedro@email.com", "password": "pass", "role": "manager"},
)

CATEGORIES = (
    {"name": "Backend", "description": "Tarefas de backend", "color": "#3498db"},
    {"name": "Frontend", "description": "Tarefas de frontend", "color": "#2ecc71"},
    {"name": "DevOps", "description": "Tarefas de infraestrutura", "color": "#e74c3c"},
    {"name": "Bug", "description": "Correção de bugs", "color": "#e67e22"},
)

#: `user` e `category` são índices em USERS/CATEGORIES; `due_in_days` é o
#: deslocamento em dias a partir de agora (negativo = task atrasada).
TASKS = (
    {
        "title": "Implementar autenticação JWT",
        "description": "Adicionar autenticação real com JWT",
        "status": "pending",
        "priority": 1,
        "user": 0,
        "category": 0,
        "due_in_days": -3,
    },
    {
        "title": "Criar tela de login",
        "description": "Tela de login responsiva",
        "status": "in_progress",
        "priority": 2,
        "user": 1,
        "category": 1,
        "due_in_days": 5,
    },
    {
        "title": "Configurar CI/CD",
        "description": "Pipeline com GitHub Actions",
        "status": "done",
        "priority": 2,
        "user": 2,
        "category": 2,
        "tags": "devops,ci,github",
    },
    {
        "title": "Corrigir bug no filtro de busca",
        "description": "Filtro não funciona com caracteres especiais",
        "status": "pending",
        "priority": 1,
        "user": 0,
        "category": 3,
        "due_in_days": -1,
    },
    {
        "title": "Adicionar paginação na API",
        "description": "Endpoints retornam todos os registros",
        "status": "pending",
        "priority": 3,
        "user": 0,
        "category": 0,
        "due_in_days": 10,
    },
    {
        "title": "Escrever testes unitários",
        "description": "Cobertura mínima de 80%",
        "status": "pending",
        "priority": 2,
        "user": 1,
        "category": 0,
    },
    {
        "title": "Documentar API com Swagger",
        "description": "Gerar documentação automática",
        "status": "cancelled",
        "priority": 4,
        "user": 2,
        "category": 0,
    },
    {
        "title": "Refatorar models",
        "description": "Melhorar organização dos models",
        "status": "in_progress",
        "priority": 3,
        "user": 1,
        "category": 0,
        "tags": "refactor,tech-debt",
    },
    {
        "title": "Configurar monitoramento",
        "description": "Prometheus + Grafana",
        "status": "pending",
        "priority": 4,
        "user": 2,
        "category": 2,
        "due_in_days": 20,
    },
    {
        "title": "Melhorar validações de input",
        "description": "Usar marshmallow ou pydantic",
        "status": "pending",
        "priority": 3,
        "user": 0,
        "category": 0,
        "tags": "improvement,validation",
    },
)


def _clear_existing():
    """Ordem inversa das dependências: tasks antes de users e categories."""
    for model in (Task, User, Category):
        db.session.query(model).delete()


def _create_users():
    users = []
    for spec in USERS:
        user = User()
        user.name = spec["name"]
        user.email = spec["email"]
        user.set_password(spec["password"])
        user.assign_role(spec["role"])
        db.session.add(user)
        users.append(user)
    return users


def _create_categories():
    categories = []
    for spec in CATEGORIES:
        category = Category()
        category.name = spec["name"]
        category.description = spec["description"]
        category.color = spec["color"]
        db.session.add(category)
        categories.append(category)
    return categories


def _create_tasks(users, categories):
    now = utcnow()
    for spec in TASKS:
        task = Task()
        task.title = spec["title"]
        task.description = spec["description"]
        task.status = spec["status"]
        task.priority = spec["priority"]
        task.user_id = users[spec["user"]].id
        task.category_id = categories[spec["category"]].id
        if "due_in_days" in spec:
            task.due_date = now + timedelta(days=spec["due_in_days"])
        if "tags" in spec:
            task.tags = spec["tags"]
        db.session.add(task)


def seed_data(app=None):
    app = create_app() if app is None else app

    with app.app_context():
        _clear_existing()
        db.session.commit()

        users = _create_users()
        categories = _create_categories()
        db.session.commit()

        _create_tasks(users, categories)
        db.session.commit()

        logger.info("Seed concluído: %s usuários, %s categorias, %s tasks",
                    len(USERS), len(CATEGORIES), len(TASKS))
        print("Seed concluído com sucesso!")
        print(f"  {len(USERS)} usuários")
        print(f"  {len(CATEGORIES)} categorias")
        print(f"  {len(TASKS)} tasks")


if __name__ == "__main__":
    seed_data()
