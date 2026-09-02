"""Fixtures compartilhadas.

Cada teste roda contra um SQLite em arquivo temporário, criado e destruído
pela fixture. Isso só é possível porque `create_app` recebe `Settings`: no
original, importar `app.py` já disparava `db.create_all()` no banco real.
"""

from __future__ import annotations

import pytest

from src.app import create_app
from src.config.settings import Settings, SmtpSettings
from src.extensions import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User

# 32+ caracteres: abaixo disso o PyJWT alerta que a chave é curta para HS256.
TEST_SECRET_KEY = "chave-apenas-para-teste-com-tamanho-suficiente"

SMTP_DISABLED = SmtpSettings(
    host="", port=587, user="", password="", timeout=5, use_tls=True
)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        environment="testing",
        debug=False,
        secret_key=TEST_SECRET_KEY,
        database_uri=f"sqlite:///{tmp_path / 'test.db'}",
        cors_origins=("http://localhost:3000",),
        jwt_expiration_minutes=60,
        bootstrap_database=True,
        host="127.0.0.1",
        port=5000,
        smtp=SMTP_DISABLED,
    )


@pytest.fixture
def app(settings):
    application = create_app(settings)
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session


def make_user(name, email, password, role="user", active=True):
    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    user.active = active
    db.session.add(user)
    return user


def make_category(name, color="#000000"):
    category = Category()
    category.name = name
    category.description = f"Categoria {name}"
    category.color = color
    db.session.add(category)
    return category


def make_task(title, **overrides):
    task = Task()
    task.title = title
    task.description = overrides.get("description", "")
    task.status = overrides.get("status", "pending")
    task.priority = overrides.get("priority", 3)
    task.user_id = overrides.get("user_id")
    task.category_id = overrides.get("category_id")
    task.due_date = overrides.get("due_date")
    task.tags = overrides.get("tags")
    db.session.add(task)
    return task


@pytest.fixture
def seeded(app):
    """Popula o banco e devolve os ids criados, sem depender do `seed.py`."""
    with app.app_context():
        admin = make_user("Admin", "admin@email.com", "1234", role="admin")
        member = make_user("Membro", "membro@email.com", "abcd", role="user")
        inactive = make_user("Inativo", "inativo@email.com", "pass", active=False)
        backend = make_category("Backend", "#3498db")
        db.session.commit()

        ids = {
            "admin_id": admin.id,
            "member_id": member.id,
            "inactive_id": inactive.id,
            "category_id": backend.id,
        }
        db.session.commit()

    return ids


def login(client, email, password):
    """Devolve o header `Authorization` de um usuário autenticado."""
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


@pytest.fixture
def admin_headers(client, seeded):
    return login(client, "admin@email.com", "1234")


@pytest.fixture
def member_headers(client, seeded):
    return login(client, "membro@email.com", "abcd")
