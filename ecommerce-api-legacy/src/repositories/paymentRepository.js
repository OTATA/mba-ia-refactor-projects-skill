'use strict';

/** Acesso à tabela `payments`. */
class PaymentRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    create({ enrollmentId, amount, status }) {
        const { lastInsertRowid } = this.#db
            .prepare(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)'
            )
            .run(enrollmentId, amount, status);

        return lastInsertRowid;
    }
}

module.exports = { PaymentRepository };
