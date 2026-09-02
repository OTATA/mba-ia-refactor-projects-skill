"""Composition root: monta a aplicação a partir das camadas.

Nenhuma rota, regra de negócio ou query vive aqui — apenas configuração,
extensões, middlewares e registro de rotas.

Diferenças em relação ao `app.py` original:

- `SECRET_KEY` vem da configuração, não de um literal no código.
- `CORS(app)` liberava todas as origens; agora as origens vêm de
  `CORS_ORIGINS` e, sem nenhuma configurada, o CORS fica desabilitado.
- `db.create_all()` deixou de rodar no import do módulo.
- `logging` configurado, substituindo os 21 `print()` espalhados no projeto.
- `create_app` permite instanciar a aplicação com configuração própria, o
  que é o que torna os testes possíveis.
"""

from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from .config.settings import Settings, load_settings
from .extensions import db
from .infrastructure.database import create_schema
from .middlewares.error_handler import register_error_handlers
from .views.routes import register_routes

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

logger = logging.getLogger(__name__)


def _configure_logging(settings):
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO, format=LOG_FORMAT
    )


def _configure_cors(app, settings):
    if settings.cors_origins:
        CORS(app, origins=list(settings.cors_origins))
        return

    logger.warning(
        "CORS desabilitado: nenhuma origem configurada. "
        "Defina CORS_ORIGINS com a lista de origens permitidas para habilitar."
    )


def create_app(settings: Settings = None):
    settings = load_settings() if settings is None else settings
    _configure_logging(settings)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        SQLALCHEMY_DATABASE_URI=settings.database_uri,
        JWT_EXPIRATION_MINUTES=settings.jwt_expiration_minutes,
        APP_ENV=settings.environment,
        HOST=settings.host,
        PORT=settings.port,
        SMTP=settings.smtp,
    )

    _configure_cors(app, settings)
    db.init_app(app)

    # Importa os models para registrar os mapeamentos antes de `create_all`.
    from . import models  # noqa: F401

    if settings.bootstrap_database:
        create_schema(app)

    register_routes(app)
    register_error_handlers(app)

    logger.info("Aplicação inicializada no ambiente '%s'", settings.environment)
    return app
