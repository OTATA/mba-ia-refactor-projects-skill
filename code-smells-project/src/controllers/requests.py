"""Leitura de entrada HTTP compartilhada pelos controllers."""

from __future__ import annotations

from flask import request

from ..exceptions import ValidacaoError


def ler_json():
    """Retorna o corpo JSON da requisição ou falha com 400.

    `silent=True` evita que um corpo ausente ou malformado escape como
    exceção não tratada — no código original isso virava HTTP 500.
    """
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        raise ValidacaoError("Dados inválidos")
    return dados


def ler_float_opcional(nome, mensagem):
    bruto = request.args.get(nome)
    if not bruto:
        return None
    try:
        return float(bruto)
    except ValueError:
        raise ValidacaoError(mensagem)
