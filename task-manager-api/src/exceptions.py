"""Erros de domínio e de aplicação.

O domínio sinaliza falhas por exceção e não conhece HTTP. A tradução para
status code acontece no error handler (`src/middlewares/error_handler.py`);
o `status_code` declarado aqui é apenas a categoria da falha.

Substitui os 12 blocos `except:` nus do código original, que devolviam
HTTP 500 sem log para qualquer problema — inclusive erros de requisição.
"""

from __future__ import annotations

from http import HTTPStatus


class DomainError(Exception):
    """Falha esperada, causada pela requisição ou pelo estado do domínio."""

    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    """Requisição malformada ou fora dos limites aceitos."""

    status_code = HTTPStatus.BAD_REQUEST


class NotFoundError(DomainError):
    """Recurso referenciado não existe."""

    status_code = HTTPStatus.NOT_FOUND


class ConflictError(DomainError):
    """Operação recusada por colidir com um registro existente."""

    status_code = HTTPStatus.CONFLICT


class UnauthorizedError(DomainError):
    """Credenciais ausentes, inválidas ou expiradas."""

    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenError(DomainError):
    """Identidade conhecida, mas sem permissão para a operação."""

    status_code = HTTPStatus.FORBIDDEN
