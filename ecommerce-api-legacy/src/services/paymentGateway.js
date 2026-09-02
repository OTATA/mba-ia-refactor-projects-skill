'use strict';

const { PaymentStatus } = require('../models/paymentStatus');

const APPROVED_CARD_PREFIX = '4';
const VISIBLE_DIGITS = 4;

/**
 * Gateway de pagamento — implementação de simulação.
 *
 * A regra de aprovação é a mesma do código original e NÃO foi alterada: cartão
 * cujo número começa com "4" é aprovado, qualquer outro é recusado. Antes ela
 * estava escondida num ternário sem nome no meio do handler HTTP; agora está
 * atrás de uma constante, num componente que pode ser substituído pela
 * integração real sem tocar no serviço de checkout.
 *
 * O que mudou é o log. O original imprimia o número completo do cartão e a
 * chave secreta do gateway em stdout:
 *
 *     console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
 *
 * Armazenar PAN em claro viola PCI-DSS, e logs normalmente são agregados,
 * replicados e retidos por terceiros. Agora só os quatro últimos dígitos
 * aparecem, e a chave nunca.
 */
class PaymentGateway {
    #apiKey;
    #logger;

    constructor({ apiKey, logger }) {
        if (!apiKey) {
            throw new Error('PaymentGateway exige uma apiKey');
        }

        // Guardada para a integração real; a simulação não transmite a chave e,
        // em nenhuma hipótese, a registra em log.
        this.#apiKey = apiKey;
        this.#logger = logger;
    }

    charge({ cardNumber, amount }) {
        this.#logger.info(
            `Processando pagamento de ${amount} no cartão ${maskCardNumber(cardNumber)}`
        );

        return cardNumber.startsWith(APPROVED_CARD_PREFIX)
            ? PaymentStatus.PAID
            : PaymentStatus.DENIED;
    }
}

function maskCardNumber(cardNumber) {
    return `****${cardNumber.slice(-VISIBLE_DIGITS)}`;
}

module.exports = { PaymentGateway };
