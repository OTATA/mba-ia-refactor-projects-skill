'use strict';

const { validateCheckoutRequest } = require('../validators/checkoutValidator');
const { checkoutCreated } = require('../views/responses');

const HTTP_OK = 200;

/**
 * `POST /api/checkout`.
 *
 * Substitui as 50 linhas de callbacks aninhados do handler original. Aqui só há
 * o fluxo de fronteira: validar a estrutura da requisição, delegar, responder.
 * Nenhum SQL, nenhuma decisão de negócio, nenhum `if (err)`.
 *
 * O handler é `async` e não captura erro: em Express 5, a rejeição chega ao
 * error handler central sozinha.
 */
class CheckoutController {
    #checkoutService;

    constructor(checkoutService) {
        this.#checkoutService = checkoutService;
    }

    handle = async (req, res) => {
        const request = validateCheckoutRequest(req.body);
        const { enrollmentId } = await this.#checkoutService.checkout(request);

        res.status(HTTP_OK).json(checkoutCreated(enrollmentId));
    };
}

module.exports = { CheckoutController };
