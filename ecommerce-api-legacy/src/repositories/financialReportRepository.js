'use strict';

/**
 * Leitura das linhas do relatório financeiro.
 *
 * Substitui o N+1 do endpoint original, que fazia `1 + C + 2E` queries — uma
 * para listar cursos, uma de matrículas por curso e mais duas (usuário e
 * pagamento) por matrícula. Com 50 cursos e 5.000 matrículas eram 10.051
 * queries por requisição.
 *
 * Agora é uma query só. Detalhes que preservam o comportamento anterior:
 *
 *  - LEFT JOIN em `enrollments`, `users` e `payments`: curso sem matrícula
 *    continua aparecendo no relatório com receita 0 e lista de alunos vazia, e
 *    matrícula órfã continua aparecendo mesmo sem usuário ou sem pagamento;
 *  - o pagamento é escolhido por `MIN(id)`. O original usava `db.get`, que
 *    devolve só a primeira linha; um JOIN direto multiplicaria a matrícula
 *    quando houvesse mais de um pagamento para ela, inflando a receita;
 *  - `e.course_id` não filtra por `active`, como no `SELECT * FROM courses`
 *    original: curso inativo aparece no relatório;
 *  - `ORDER BY` torna a saída determinística, no lugar da ordem de conclusão
 *    dos callbacks.
 */

const REPORT_QUERY = `
    SELECT
        c.id       AS courseId,
        c.title    AS courseTitle,
        e.id       AS enrollmentId,
        u.id       AS studentId,
        u.name     AS studentName,
        p.id       AS paymentId,
        p.amount   AS paymentAmount,
        p.status   AS paymentStatus
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.id = (
        SELECT MIN(inner_payment.id)
        FROM payments inner_payment
        WHERE inner_payment.enrollment_id = e.id
    )
    ORDER BY c.id, e.id
`;

class FinancialReportRepository {
    #db;

    constructor(db) {
        this.#db = db;
    }

    findReportRows() {
        return this.#db.prepare(REPORT_QUERY).all();
    }
}

module.exports = { FinancialReportRepository };
