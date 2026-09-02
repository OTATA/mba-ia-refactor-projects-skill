'use strict';

/**
 * Status de um pagamento.
 *
 * Substitui as strings soltas `'PAID'` e `'DENIED'`, que apareciam duplicadas
 * no checkout e no relatório financeiro sem nenhuma constante ligando as duas
 * pontas.
 */

const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

/** Só pagamento aprovado soma receita — regra do relatório original. */
function isApproved(status) {
    return status === PaymentStatus.PAID;
}

module.exports = { PaymentStatus, isApproved };
