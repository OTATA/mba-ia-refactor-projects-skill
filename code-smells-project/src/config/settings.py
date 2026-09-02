"""Configuração da aplicação, lida exclusivamente do ambiente.

Nenhum segredo é definido no código. Em produção a ausência de `SECRET_KEY`
interrompe o boot; em desenvolvimento uma chave efêmera é gerada para que
`python app.py` continue funcionando sem setup extra.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

APP_VERSION = "1.0.0"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _read_bool(env, name, default):
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def _read_int(env, name, default):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _read_origins(env):
    raw = env.get("CORS_ORIGINS", "")
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    debug: bool
    secret_key: str
    database_path: str
    cors_origins: tuple
    bootstrap_database: bool
    seed_database: bool
    host: str
    port: int

    @property
    def is_production(self):
        return self.environment == "production"


def load_settings(env=None):
    env = os.environ if env is None else env

    environment = env.get("APP_ENV", "development").strip().lower()
    is_production = environment == "production"

    secret_key = env.get("SECRET_KEY", "").strip()
    if not secret_key:
        if is_production:
            raise RuntimeError(
                "SECRET_KEY é obrigatória quando APP_ENV=production. "
                "Defina a variável de ambiente antes de iniciar a aplicação."
            )
        secret_key = secrets.token_urlsafe(32)

    return Settings(
        environment=environment,
        debug=_read_bool(env, "APP_DEBUG", not is_production),
        secret_key=secret_key,
        database_path=env.get("DATABASE_PATH", "loja.db"),
        cors_origins=_read_origins(env),
        bootstrap_database=_read_bool(env, "BOOTSTRAP_DATABASE", not is_production),
        seed_database=_read_bool(env, "SEED_DATABASE", not is_production),
        host=env.get("APP_HOST", "127.0.0.1"),
        port=_read_int(env, "APP_PORT", 5000),
    )
