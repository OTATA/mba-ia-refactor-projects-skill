'use strict';

const { ValidationError } = require('../errors');

const BAD_REQUEST_MESSAGE = 'Bad Request';

/**
 * Validação do payload de checkout.
 *
 * Os nomes dos campos (`usr`, `eml`, `pwd`, `c_id`, `card`) são abreviações
 * ruins, mas fazem parte do contrato público documentado em `api.http` e foram
 * preservados. A tradução para nomes de domínio acontece aqui, na fronteira, e
 * nenhuma camada interna volta a ver `c_id` ou `eml`.
 *
 * A validação original era `if (!u || !e || !cid || !cc)`, ou seja, só
 * truthiness. Um `card` numérico no JSON passava por ela e explodia adiante em
 * `cc.startsWith(...)`, dentro de um callback do driver sqlite3 — um TypeError
 * fora do alcance do Express, que virava `uncaughtException` e derrubava o
 * processo inteiro (e, com o banco em memória, todos os dados). Um único
 * request malformado bastava. Agora o tipo é conferido antes de qualquer I/O.
 *
 * Nada é normalizado: `trim` em `pwd` mudaria a credencial derivada e `trim` em
 * `eml` mudaria a busca por usuário existente. Os valores seguem como chegaram,
 * como no código original.
 *
 * Status e mensagem continuam 400 'Bad Request', como antes.
 */
function validateCheckoutRequest(body) {
    const payload = body ?? {};

    const name = readRequiredString(payload.usr);
    const email = readRequiredString(payload.eml);
    const courseId = readCourseId(payload.c_id);
    const cardNumber = readRequiredString(payload.card);
    // `pwd` é opcional: o serviço aplica o default quando não vem.
    const password = readOptionalString(payload.pwd);

    if (!name || !email || !courseId || !cardNumber) {
        throw new ValidationError(BAD_REQUEST_MESSAGE);
    }

    return { name, email, courseId, cardNumber, password };
}

/** Ausente vira string vazia para cair na checagem de obrigatoriedade. */
function readRequiredString(value) {
    if (value === undefined || value === null) return '';

    assertString(value);
    return value;
}

/**
 * Distingue "ausente" de "presente com tipo errado".
 *
 * A diferença importa: ausente usa o default de senha, tipo errado precisa
 * virar 400. Tratar os dois como ausente faria um `pwd` numérico cair
 * silenciosamente no default '123456' — o cliente acreditaria ter definido uma
 * senha que não foi a gravada.
 */
function readOptionalString(value) {
    if (value === undefined || value === null) return undefined;

    assertString(value);
    return value;
}

function assertString(value) {
    if (typeof value !== 'string') {
        throw new ValidationError(BAD_REQUEST_MESSAGE);
    }
}

/**
 * Aceita inteiro positivo ou string numérica — `api.http` envia número, mas o
 * SQLite coagia string no código original, então as duas formas já funcionavam.
 */
function readCourseId(value) {
    if (value === undefined || value === null) return null;

    if (typeof value !== 'number' && typeof value !== 'string') {
        throw new ValidationError(BAD_REQUEST_MESSAGE);
    }

    const courseId = typeof value === 'string' ? Number(value) : value;

    return Number.isInteger(courseId) && courseId > 0 ? courseId : null;
}

module.exports = { validateCheckoutRequest };
