'use strict';

const { Course } = require('../models/course');

/**
 * Acesso à tabela `courses`.
 *
 * As colunas são listadas explicitamente em vez de `SELECT *`: uma coluna nova
 * no schema não passa a trafegar sozinha até a camada de resposta.
 */
class CourseRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    /**
     * O filtro `active = 1` é a regra original de compra e continua no SQL para
     * que curso inativo nem chegue ao serviço.
     */
    findPurchasableById(id) {
        const row = this.#db
            .prepare(
                'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1'
            )
            .get(id);

        return Course.fromRow(row);
    }
}

module.exports = { CourseRepository };
