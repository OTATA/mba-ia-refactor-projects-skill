"""Controller de autenticação.

O corpo da resposta mantém as três chaves originais (`message`, `user`,
`token`), com duas diferenças: `user` não traz mais o hash da senha, e
`token` é um JWT assinado com expiração em vez de
`'fake-jwt-token-' + str(user.id)`.
"""

from __future__ import annotations

from ..services import auth_service
from ..validators import user_validator
from ..views import responses, serializers
from .requests import read_json


def login():
    email, password = user_validator.validate_credentials(read_json())
    user, token = auth_service.authenticate(email, password)

    return responses.ok(
        {
            "message": "Login realizado com sucesso",
            "user": serializers.serialize_user(user),
            "token": token,
        }
    )
