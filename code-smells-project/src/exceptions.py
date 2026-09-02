"""Erros de domínio e de aplicação.

O domínio sinaliza falhas por exceção e não conhece HTTP. A tradução para
status code acontece no error handler (`src/middlewares/error_handler.py`);
o `status_code` declarado aqui é apenas a categoria da falha.
"""


class DomainError(Exception):
    """Falha esperada, causada pela requisição ou pelo estado do domínio."""

    status_code = 400

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ValidacaoError(DomainError):
    """Requisição malformada ou fora dos limites aceitos."""

    status_code = 400


class RegraDeNegocioError(DomainError):
    """Operação recusada por uma regra de negócio (ex.: estoque insuficiente)."""

    status_code = 400


class NaoEncontradoError(DomainError):
    """Recurso referenciado não existe."""

    status_code = 404


class CredenciaisInvalidasError(DomainError):
    """Par email/senha não confere."""

    status_code = 401
