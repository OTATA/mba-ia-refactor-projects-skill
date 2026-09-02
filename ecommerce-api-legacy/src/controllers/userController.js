'use strict';

const { ValidationError } = require('../errors');
const { userDeleted } = require('../views/responses');

const BAD_REQUEST_MESSAGE = 'Bad Request';

/**
 * `DELETE /api/users/:id`.
 *
 * ATENÇÃO — débito de segurança registrado na auditoria: qualquer requisição
 * não autenticada pode apagar qualquer usuário, inclusive em massa iterando
 * ids. Continua aberto porque adicionar autenticação seria comportamento novo,
 * fora do escopo desta refatoração.
 */
class UserController {
    #userService;

    constructor(userService) {
        this.#userService = userService;
    }

    remove = (req, res) => {
        const id = parseId(req.params.id);
        if (id === null) {
            throw new ValidationError(BAD_REQUEST_MESSAGE);
        }

        this.#userService.delete(id);

        res.send(userDeleted());
    };
}

function parseId(raw) {
    const id = Number(raw);

    return Number.isInteger(id) && id > 0 ? id : null;
}

module.exports = { UserController };
