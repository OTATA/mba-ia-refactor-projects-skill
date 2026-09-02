'use strict';

/**
 * Acesso à tabela `users`.
 *
 * Nenhum método devolve a coluna `pass`: o hash não sai da camada de
 * persistência, então não há como vazá-lo por serialização acidental de uma
 * entidade na resposta.
 */
class UserRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    /**
     * Preserva a consulta original (`SELECT id FROM users WHERE email = ?`),
     * usada pelo checkout para decidir entre reaproveitar e criar o usuário.
     */
    findIdByEmail(email) {
        const row = this.#db
            .prepare('SELECT id FROM users WHERE email = ?')
            .get(email);

        return row ? row.id : null;
    }

    create({ name, email, passwordHash }) {
        const { lastInsertRowid } = this.#db
            .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
            .run(name, email, passwordHash);

        return lastInsertRowid;
    }

    /**
     * Matrículas e pagamentos do usuário saem junto, por `ON DELETE CASCADE`
     * declarado no schema — o SQLite executa a cascata na mesma transação
     * implícita do `DELETE`.
     */
    deleteById(id) {
        const { changes } = this.#db
            .prepare('DELETE FROM users WHERE id = ?')
            .run(id);

        return changes;
    }
}

module.exports = { UserRepository };
