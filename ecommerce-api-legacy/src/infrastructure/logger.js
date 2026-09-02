'use strict';

/**
 * Logger mínimo da aplicação.
 *
 * Existe para dar um ponto único de saída de log — o código original espalhava
 * `console.log` pelas camadas, inclusive imprimindo número de cartão e chave do
 * gateway. Concentrar aqui é o que permite trocar por um logger estruturado
 * (pino, winston) sem tocar em serviço nenhum.
 */

function createLogger(output = console) {
    return {
        info(message) {
            output.log(`[INFO] ${message}`);
        },
        warn(message) {
            output.warn(`[WARN] ${message}`);
        },
        error(message, error) {
            // A stack fica no log do servidor; o cliente recebe mensagem
            // genérica pelo error handler.
            output.error(`[ERROR] ${message}`, error ?? '');
        },
    };
}

module.exports = { createLogger };
