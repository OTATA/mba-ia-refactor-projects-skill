'use strict';

const Database = require('better-sqlite3');

const { IN_MEMORY_DATABASE } = require('../config/settings');

/**
 * Abertura da conexão SQLite.
 *
 * O driver `sqlite3` foi trocado por `better-sqlite3` por dois motivos:
 *
 *  - o repositório do `sqlite3` está oficialmente sem manutenção ("This
 *    repository is currently unmaintained. We will not update any of its issues
 *    or pull requests."), ou seja, sem garantia de correção de segurança;
 *  - a API síncrona do `better-sqlite3` dá transação real via `db.transaction()`.
 *    Era exatamente o que faltava no checkout original, que gravava matrícula,
 *    pagamento e log de auditoria em três autocommits separados, e o que
 *    elimina de uma vez o callback hell e os contadores manuais de conclusão.
 */

function createConnection({ databasePath, sqlDebug = false }) {
    const db = new Database(databasePath, sqlDebug ? { verbose: console.log } : {});

    // Precisa ser habilitado por conexão: com o pragma desligado — que é o
    // default do SQLite — as cláusulas FOREIGN KEY do schema são aceitas na
    // criação da tabela e simplesmente ignoradas na hora de gravar.
    db.pragma('foreign_keys = ON');

    // WAL não se aplica a banco em memória.
    if (databasePath !== IN_MEMORY_DATABASE) {
        db.pragma('journal_mode = WAL');
    }

    return db;
}

module.exports = { createConnection };
