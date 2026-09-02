"""Validação do payload de task.

No original as mesmas regras estavam escritas duas vezes — `create_task`
(`routes/task_routes.py:96-124`) e `update_task` (`:166-198`) — com mensagens
divergentes, e uma terceira versão morta em `utils/helpers.process_task_data`.

As mensagens de erro e a *ordem* das checagens são idênticas às originais,
para que a precedência dos erros não mude. A diferença é que tipos errados
agora viram HTTP 400 em vez de HTTP 500: `{"priority": "alta"}` levantava
`TypeError` na comparação `priority < 1`, e `{"title": null}` levantava
`TypeError` em `len(data['title'])`.
"""

from __future__ import annotations

from datetime import datetime

from ..exceptions import ValidationError
from ..models.enums import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    DUE_DATE_FORMAT,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TaskStatus,
)
from ..models.task import TAG_SEPARATOR

MESSAGE_TITLE_REQUIRED = "Título é obrigatório"
MESSAGE_TITLE_INVALID = "Título inválido"
MESSAGE_TITLE_TOO_SHORT = "Título muito curto"
MESSAGE_TITLE_TOO_LONG = "Título muito longo"
MESSAGE_INVALID_STATUS = "Status inválido"
MESSAGE_PRIORITY_INVALID = "Prioridade inválida"
MESSAGE_PRIORITY_OUT_OF_RANGE = "Prioridade deve ser entre 1 e 5"
MESSAGE_INVALID_TAGS = "Tags inválidas"
MESSAGE_INVALID_REFERENCE = "Identificador inválido"

#: `create_task` e `update_task` usavam mensagens diferentes para a mesma
#: falha de data; ambas são preservadas.
MESSAGE_DATE_FORMAT_ON_CREATE = "Formato de data inválido. Use YYYY-MM-DD"
MESSAGE_DATE_FORMAT_ON_UPDATE = "Formato de data inválido"


def _validate_title(value, missing_message):
    # Checagem por falsidade, igual ao `if not title` original: `None`, `""`
    # e `0` produzem a mesma mensagem de antes.
    if not value:
        raise ValidationError(missing_message)
    if not isinstance(value, str):
        raise ValidationError(MESSAGE_TITLE_INVALID)
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError(MESSAGE_TITLE_TOO_SHORT)
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError(MESSAGE_TITLE_TOO_LONG)
    return value


def _validate_status(value):
    if not TaskStatus.is_valid(value):
        raise ValidationError(MESSAGE_INVALID_STATUS)
    return value


def _validate_priority(value):
    # `isinstance(True, int)` é verdadeiro em Python; booleano não é prioridade.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(MESSAGE_PRIORITY_INVALID)
    if not MIN_PRIORITY <= value <= MAX_PRIORITY:
        raise ValidationError(MESSAGE_PRIORITY_OUT_OF_RANGE)
    return value


def _validate_reference(value):
    """Valida `user_id`/`category_id`. `None` é aceito e desatribui."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(MESSAGE_INVALID_REFERENCE)
    return value


def _validate_due_date(value, format_message):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValidationError(format_message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(format_message)


def _validate_tags(value):
    """Normaliza para a string separada por vírgula que o schema guarda."""
    if value is None:
        return None
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError(MESSAGE_INVALID_TAGS)
        return TAG_SEPARATOR.join(value)
    if isinstance(value, str):
        return value
    raise ValidationError(MESSAGE_INVALID_TAGS)


def validate_create_payload(data):
    """Normaliza o corpo de `POST /tasks`.

    A ordem das checagens reproduz a original: título, status, prioridade,
    referências, data, tags.
    """
    title = _validate_title(data.get("title"), MESSAGE_TITLE_REQUIRED)
    status = _validate_status(data.get("status", DEFAULT_STATUS))
    priority = _validate_priority(data.get("priority", DEFAULT_PRIORITY))

    return {
        "title": title,
        "description": data.get("description", ""),
        "status": status,
        "priority": priority,
        "user_id": _validate_reference(data.get("user_id")),
        "category_id": _validate_reference(data.get("category_id")),
        "due_date": _validate_due_date(
            data.get("due_date"), MESSAGE_DATE_FORMAT_ON_CREATE
        ),
        "tags": _validate_tags(data.get("tags")),
    }


def validate_update_payload(data):
    """Normaliza o corpo de `PUT /tasks/<id>`.

    Atualização parcial: só os campos presentes entram no resultado, para
    distinguir "não informado" de "informado como null" — a mesma semântica
    dos `if 'campo' in data` do original.
    """
    changes = {}

    if "title" in data:
        # O original só checava o comprimento no update, então `""` caía em
        # "Título muito curto" em vez de "Título é obrigatório".
        changes["title"] = _validate_title(data["title"], MESSAGE_TITLE_TOO_SHORT)

    if "description" in data:
        changes["description"] = data["description"]

    if "status" in data:
        changes["status"] = _validate_status(data["status"])

    if "priority" in data:
        changes["priority"] = _validate_priority(data["priority"])

    if "user_id" in data:
        changes["user_id"] = _validate_reference(data["user_id"])

    if "category_id" in data:
        changes["category_id"] = _validate_reference(data["category_id"])

    if "due_date" in data:
        changes["due_date"] = _validate_due_date(
            data["due_date"], MESSAGE_DATE_FORMAT_ON_UPDATE
        )

    if "tags" in data:
        changes["tags"] = _validate_tags(data["tags"])

    return changes
