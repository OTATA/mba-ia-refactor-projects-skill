"""Composition root: monta a aplicação a partir das camadas.

Nenhuma rota, regra de negócio ou SQL vive aqui — apenas configuração,
middlewares e registro de rotas.
"""

from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from .config.settings import Settings, load_settings
from .infrastructure.database import close_connection
from .infrastructure.schema import bootstrap
from .middlewares.error_handler import registrar_error_handlers
from .views.routes import registrar_rotas

FORMATO_LOG = "%(asctime)s %(levelname)s %(name)s %(message)s"

logger = logging.getLogger(__name__)


def _configurar_logging(settings):
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO, format=FORMATO_LOG
    )


def _configurar_cors(app, settings):
    if settings.cors_origins:
        CORS(app, origins=list(settings.cors_origins))
        return

    logger.warning(
        "CORS desabilitado: nenhuma origem configurada. "
        "Defina CORS_ORIGINS com a lista de origens permitidas para habilitar."
    )


def create_app(settings: Settings = None):
    settings = load_settings() if settings is None else settings
    _configurar_logging(settings)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        DATABASE_PATH=settings.database_path,
        APP_ENV=settings.environment,
        HOST=settings.host,
        PORT=settings.port,
    )

    _configurar_cors(app, settings)
    app.teardown_appcontext(close_connection)

    if settings.bootstrap_database:
        if bootstrap(settings.database_path, seed=settings.seed_database):
            logger.info("Banco populado com os dados de exemplo")

    registrar_rotas(app)
    registrar_error_handlers(app)

    logger.info("Aplicação inicializada no ambiente '%s'", settings.environment)
    return app
