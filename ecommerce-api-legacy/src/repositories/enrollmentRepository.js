'use strict';

/** Acesso à tabela `enrollments`. */
class EnrollmentRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    /**
     * Devolve o id gerado explicitamente. No original, o id vinha de
     * `this.lastID` dentro de um callback declarado com `function`, o que
     * rebindava `this` e forçava o `const self = this` do método — trocar por
     * arrow function ali quebrava o código em silêncio.
     */
    create({ userId, courseId }) {
        const { lastInsertRowid } = this.#db
            .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
            .run(userId, courseId);

        return lastInsertRowid;
    }
}

module.exports = { EnrollmentRepository };
