'use strict';

const { isApproved } = require('./paymentStatus');

const UNKNOWN_STUDENT = 'Unknown';
const NO_PAYMENT_AMOUNT = 0;

/**
 * Agregação do relatório financeiro.
 *
 * Concentra as regras que antes estavam diluídas nos quatro níveis de callback
 * de `AppManager.setupRoutes`, junto de contadores manuais de concorrência:
 *
 *  1. só pagamento com status PAID soma receita;
 *  2. o aluno aparece na listagem independentemente do status do pagamento;
 *  3. matrícula sem pagamento registrado aparece com `paid: 0`;
 *  4. matrícula cujo usuário não existe mais aparece como 'Unknown'.
 *
 * A regra 4 existe porque `DELETE /api/users/:id` deixava matrículas órfãs no
 * banco. O saneamento das foreign keys impede que novos órfãos apareçam, mas a
 * regra é mantida para não quebrar a leitura de bases já corrompidas.
 *
 * A ordem dos cursos agora é determinística (segue o `ORDER BY` da query). No
 * original, `report.push` acontecia na ordem de conclusão das queries, então
 * duas chamadas idênticas podiam devolver os cursos em ordens diferentes.
 */
class FinancialReport {
    /**
     * Monta o relatório a partir das linhas achatadas do JOIN.
     *
     * As linhas vêm ordenadas por curso; cursos sem matrícula chegam com as
     * colunas de matrícula nulas por conta do LEFT JOIN.
     */
    static fromRows(rows) {
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.courseId)) {
                byCourse.set(row.courseId, {
                    course: row.courseTitle,
                    revenue: 0,
                    students: [],
                });
            }

            if (row.enrollmentId === null) continue;

            const course = byCourse.get(row.courseId);

            // Testamos o id, e não `amount`/`name`, para distinguir "linha
            // ausente" de "coluna nula", exatamente como os `payment ? ... : ...`
            // e `user ? ... : ...` do código original.
            const hasPayment = row.paymentId !== null;
            const hasStudent = row.studentId !== null;

            if (hasPayment && isApproved(row.paymentStatus)) {
                course.revenue += row.paymentAmount;
            }

            course.students.push({
                student: hasStudent ? row.studentName : UNKNOWN_STUDENT,
                paid: hasPayment ? row.paymentAmount : NO_PAYMENT_AMOUNT,
            });
        }

        return new FinancialReport([...byCourse.values()]);
    }

    constructor(courses) {
        this.courses = courses;
        Object.freeze(this);
    }
}

module.exports = { FinancialReport };
