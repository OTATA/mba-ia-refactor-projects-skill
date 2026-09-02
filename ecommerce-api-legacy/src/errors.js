'use strict';

/**
 * Erros de domínio e de aplicação.
 *
 * O domínio sinaliza falha por exceção e não conhece HTTP: nenhuma camada
 * abaixo dos controllers toca `res`. A tradução para resposta acontece em
 * `src/middlewares/errorHandler.js`.
 *
 * O `status` declarado aqui é a categoria da falha, mantida junto do erro para
 * evitar um mapa paralelo erro→status que sai de sincronia com o tempo.
 */

class DomainError extends Error {
    static status = 400;

    constructor(message) {
        super(message);
        this.name = this.constructor.name;
        this.status = this.constructor.status;
    }
}

/** Payload malformado ou fora dos tipos aceitos. */
class ValidationError extends DomainError {
    static status = 400;
}

/** Recurso referenciado não existe. */
class NotFoundError extends DomainError {
    static status = 404;
}

/**
 * Pagamento recusado pelo gateway.
 *
 * Mantém 400 para não quebrar o contrato existente, ainda que 402 fosse
 * semanticamente mais correto — a requisição em si é válida.
 */
class PaymentDeclinedError extends DomainError {
    static status = 400;
}

module.exports = {
    DomainError,
    ValidationError,
    NotFoundError,
    PaymentDeclinedError,
};
