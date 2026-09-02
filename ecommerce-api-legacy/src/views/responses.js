'use strict';

/**
 * Representação das respostas da API.
 *
 * Numa API REST a responsabilidade de View aparece como presenters: é aqui que
 * o formato externo é decidido, e só aqui. Nenhum controller monta corpo de
 * resposta na mão.
 *
 * O formato dos endpoints originais foi mantido byte a byte para não quebrar
 * clientes existentes — inclusive o `send` com string, que o Express serve como
 * `text/html`, e o campo `enrollment_id` em snake_case. Centralizar aqui é
 * justamente o que permite migrar para um envelope JSON de erro depois, num
 * único ponto.
 */

const CHECKOUT_SUCCESS_MESSAGE = 'Sucesso';
const USER_DELETED_MESSAGE = 'Usuário deletado';

/** `{ msg: 'Sucesso', enrollment_id: 7 }` — igual ao original. */
function checkoutCreated(enrollmentId) {
    return { msg: CHECKOUT_SUCCESS_MESSAGE, enrollment_id: enrollmentId };
}

/** Array de `{ course, revenue, students: [{ student, paid }] }`. */
function financialReport(report) {
    return report.courses;
}

/**
 * A mensagem original ("Usuário deletado, mas as matrículas e pagamentos
 * ficaram sujos no banco.") descrevia o bug de integridade que foi corrigido —
 * mantê-la agora seria falso. O status 200 continua o mesmo.
 */
function userDeleted() {
    return USER_DELETED_MESSAGE;
}

/** Erro em texto puro, como nos handlers originais. */
function sendError(res, status, message) {
    res.status(status).send(message);
}

module.exports = {
    checkoutCreated,
    financialReport,
    userDeleted,
    sendError,
};
