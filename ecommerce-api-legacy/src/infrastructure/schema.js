'use strict';

/**
 * Schema do banco.
 *
 * As tabelas e colunas são as mesmas do `AppManager.initDb`, com três adições
 * que corrigem problemas de integridade encontrados na auditoria:
 *
 *  - FOREIGN KEYs: o schema original não declarava nenhuma. `DELETE` de usuário
 *    deixava matrículas e pagamentos apontando para um id inexistente — a
 *    própria resposta do endpoint admitia isso. `ON DELETE CASCADE` remove os
 *    dependentes junto, na transação implícita do próprio `DELETE`.
 *    Se a contabilidade exigir preservar o histórico de pagamentos, troque por
 *    `ON DELETE RESTRICT`: o delete passa a falhar quando houver matrícula.
 *
 *  - NOT NULL / UNIQUE: o checkout já tratava e-mail como identificador único
 *    (procurava por e-mail e só criava o usuário se não achasse), mas nada
 *    impedia duplicata em caso de requisições concorrentes. Agora o banco
 *    garante o invariante.
 *
 *  - índices nas colunas de junção, usadas pelo relatório financeiro.
 *
 * `IF NOT EXISTS` permite reabrir um banco em arquivo sem recriar nada — o
 * original só funcionava com banco em memória recém-criado.
 */

const SCHEMA_STATEMENTS = `
CREATE TABLE IF NOT EXISTS users (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id     INTEGER PRIMARY KEY,
    title  TEXT NOT NULL,
    price  REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS enrollments (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments (id) ON DELETE CASCADE,
    amount        REAL NOT NULL,
    status        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY,
    action     TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments (user_id);
CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON payments (enrollment_id);
`;

/**
 * Cria o schema.
 *
 * `exec` propaga erro de DDL por exceção. No original, nenhum dos `db.run` do
 * `initDb` verificava o callback de erro: uma falha de criação de tabela passava
 * despercebida e a aplicação subia com schema incompleto.
 */
function createSchema(db) {
    db.exec(SCHEMA_STATEMENTS);
}

module.exports = { createSchema };
