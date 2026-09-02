'use strict';

/**
 * Acesso à tabela `audit_logs`.
 *
 * O registro é gravado dentro da transação do checkout. No original, o erro
 * deste `INSERT` era recebido e descartado, e a API respondia `200 Sucesso` de
 * qualquer forma — um checkout podia ficar sem trilha de auditoria sem que
 * ninguém soubesse.
 */
class AuditLogRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    record(action) {
        const { lastInsertRowid } = this.#db
            .prepare(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))"
            )
            .run(action);

        return lastInsertRowid;
    }
}

module.exports = { AuditLogRepository };
