"""Construção das respostas HTTP.

Um único ponto define os formatos, no lugar dos `jsonify(...), <status>`
repetidos em cada um dos 22 handlers originais.

O envelope é deliberadamente o mesmo de antes — payload cru, sem wrapper —
para não quebrar os clientes: listagens devolvem um array JSON no topo,
recursos devolvem o objeto, mensagens devolvem `{"message": ...}` e erros
devolvem `{"error": ...}`.
"""

from __future__ import annotations

from http import HTTPStatus

from flask import jsonify

STATUS_OK = HTTPStatus.OK
STATUS_CREATED = HTTPStatus.CREATED


def ok(payload):
    return jsonify(payload), int(STATUS_OK)


def created(payload):
    return jsonify(payload), int(STATUS_CREATED)


def message(text, status=STATUS_OK):
    return jsonify({"message": text}), int(status)


def error(text, status):
    return jsonify({"error": text}), int(status)
