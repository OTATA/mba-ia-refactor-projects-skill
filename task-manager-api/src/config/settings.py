"""Configuração da aplicação, lida exclusivamente do ambiente.

Substitui os valores fixos do `app.py` original, que traziam
`SECRET_KEY = 'super-secret-key-123'` versionado no Git, e as credenciais SMTP
hardcoded em `services/notification_service.py`.

Nenhum segredo é definido no código. Em produção a ausência de `SECRET_KEY`
interrompe o boot; em desenvolvimento uma chave efêmera é gerada para que
`python app.py` continue funcionando sem setup extra.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

APP_NAME = "Task Manager API"
APP_VERSION = "1.0"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

#: HS256 usa HMAC-SHA256; o RFC 7518 §3.2 exige uma chave de pelo menos 256
#: bits. A `SECRET_KEY` do original tinha 21 caracteres.
MIN_SECRET_KEY_LENGTH = 32


def _read_bool(env, name, default):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in _TRUTHY


def _read_int(env, name, default):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _read_str(env, name, default=""):
    raw = env.get(name)
    return default if raw is None else raw.strip()


def _read_origins(env):
    raw = env.get("CORS_ORIGINS", "")
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@dataclass(frozen=True)
class SmtpSettings:
    """Credenciais do servidor de e-mail. Sem `host`, o envio é só logado."""

    host: str
    port: int
    user: str
    password: str
    timeout: int
    use_tls: bool

    @property
    def is_configured(self):
        return bool(self.host and self.user)


@dataclass(frozen=True)
class Settings:
    environment: str
    debug: bool
    secret_key: str
    database_uri: str
    cors_origins: tuple
    jwt_expiration_minutes: int
    bootstrap_database: bool
    host: str
    port: int
    smtp: SmtpSettings

    @property
    def is_production(self):
        return self.environment == "production"


def load_settings(env=None):
    if env is None:
        load_dotenv()
        env = os.environ

    environment = _read_str(env, "APP_ENV", "development").lower()
    is_production = environment == "production"

    secret_key = _read_str(env, "SECRET_KEY")
    if not secret_key:
        if is_production:
            raise RuntimeError(
                "SECRET_KEY é obrigatória quando APP_ENV=production. "
                "Defina a variável de ambiente antes de iniciar a aplicação."
            )
        # Chave efêmera: os tokens emitidos não sobrevivem a um restart, o que
        # é aceitável em desenvolvimento e preferível a um segredo no código.
        secret_key = secrets.token_urlsafe(MIN_SECRET_KEY_LENGTH)
    elif is_production and len(secret_key) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"SECRET_KEY precisa de ao menos {MIN_SECRET_KEY_LENGTH} caracteres "
            "para assinar tokens HS256 com segurança. Gere uma com: "
            'python -c "import secrets; print(secrets.token_urlsafe(32))"'
        )

    return Settings(
        environment=environment,
        debug=_read_bool(env, "APP_DEBUG", not is_production),
        secret_key=secret_key,
        database_uri=_read_str(env, "DATABASE_URI", "sqlite:///tasks.db"),
        cors_origins=_read_origins(env),
        jwt_expiration_minutes=_read_int(env, "JWT_EXPIRATION_MINUTES", 60),
        bootstrap_database=_read_bool(env, "BOOTSTRAP_DATABASE", not is_production),
        # 127.0.0.1 em vez do 0.0.0.0 original: o servidor de desenvolvimento
        # não deve escutar em todas as interfaces da rede.
        host=_read_str(env, "APP_HOST", "127.0.0.1"),
        port=_read_int(env, "APP_PORT", 5000),
        smtp=SmtpSettings(
            host=_read_str(env, "SMTP_HOST"),
            port=_read_int(env, "SMTP_PORT", 587),
            user=_read_str(env, "SMTP_USER"),
            password=_read_str(env, "SMTP_PASSWORD"),
            timeout=_read_int(env, "SMTP_TIMEOUT", 10),
            use_tls=_read_bool(env, "SMTP_USE_TLS", True),
        ),
    )
