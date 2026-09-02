"""Orquestração dos casos de uso de usuário e autenticação."""

from __future__ import annotations

import logging

from ..exceptions import CredenciaisInvalidasError, NaoEncontradoError, ValidacaoError
from ..infrastructure.database import transaction
from ..models.usuario import Usuario

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, usuario_repository):
        self._usuarios = usuario_repository

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NaoEncontradoError("Usuário não encontrado")
        return usuario

    def criar(self, nome, email, senha):
        if not nome or not email or not senha:
            raise ValidacaoError("Nome, email e senha são obrigatórios")

        usuario = Usuario.novo(nome=nome, email=email, senha=senha)
        with transaction():
            usuario_id = self._usuarios.criar(usuario)
        logger.info("Usuário criado com id %s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        if not email or not senha:
            raise ValidacaoError("Email e senha são obrigatórios")

        usuario = self._usuarios.buscar_por_email(email)
        if usuario is None or not usuario.senha_confere(senha):
            logger.info("Tentativa de login recusada")
            raise CredenciaisInvalidasError("Email ou senha inválidos")

        logger.info("Login bem-sucedido para o usuário %s", usuario.id)
        return usuario
