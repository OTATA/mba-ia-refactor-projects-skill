'use strict';

/**
 * Operações sobre usuários.
 *
 * Comportamento preservado: a exclusão responde sucesso mesmo quando o id não
 * existe. O handler original ignorava o erro do `DELETE` e respondia 200 em
 * qualquer caso; devolver 404 aqui mudaria o contrato do endpoint.
 *
 * Mudança deliberada de comportamento: o `DELETE` original removia apenas a
 * linha de `users` e deixava matrículas e pagamentos apontando para um usuário
 * inexistente — a própria mensagem de resposta admitia isso ("as matrículas e
 * pagamentos ficaram sujos no banco"). Com as foreign keys declaradas em
 * `src/infrastructure/schema.js`, os dependentes saem junto. Se a contabilidade
 * exigir preservar o histórico de pagamentos, troque `ON DELETE CASCADE` por
 * `ON DELETE RESTRICT` no schema.
 */
class UserService {
    #users;

    constructor(userRepository) {
        this.#users = userRepository;
    }

    delete(id) {
        return this.#users.deleteById(id);
    }
}

module.exports = { UserService };
