'use strict';

const { DomainError } = require('../errors');
const { sendError } = require('../views/responses');

const INTERNAL_SERVER_ERROR = 500;
const INTERNAL_ERROR_MESSAGE = 'Erro interno do servidor';
const MIN_CLIENT_ERROR = 400;
const MAX_CLIENT_ERROR = 499;

/**
 * Tratamento centralizado de erros.
 *
 * Substitui os `if (err) return res.status(500).send("Erro DB")` espalhados
 * pelos callbacks do `AppManager` e, pior, os pontos em que o erro era recebido
 * e simplesmente descartado — log de auditoria, leitura de matrículas, delete de
 * usuário —, fazendo a API responder sucesso para operações que não
 * aconteceram e sem deixar rastro em log nenhum.
 *
 * São três casos, nesta ordem:
 *
 *  1. erro de domínio: vira a resposta que o próprio domínio declarou;
 *  2. erro de cliente vindo de middleware (o `express.json()` rejeita JSON
 *     malformado com `status: 400` e `expose: true`): o status do erro é
 *     respeitado. Sem este caso, corpo malformado virava 500 — o Express 4
 *     original respondia 400 pelo handler default, então tratar tudo que não é
 *     `DomainError` como 500 seria uma regressão de contrato;
 *  3. qualquer outra falha: vai para o log do servidor com stack e o cliente
 *     recebe mensagem genérica. As mensagens originais ("Erro DB", "Erro
 *     Matrícula") não diziam nada ao cliente e, em outras rotas, a mensagem
 *     crua do SQLite vazava.
 *
 * Em Express 5, handler `async` que rejeita chega aqui automaticamente — a
 * documentação oficial garante que "route handlers and middleware that return a
 * Promise call `next(value)` automatically when they reject or throw an error".
 * Era isso que faltava no original: exceção lançada dentro de callback do driver
 * não passava pelo Express e derrubava o processo.
 */
function createErrorHandler(logger) {
    return function errorHandler(error, req, res, next) {
        if (res.headersSent) {
            return next(error);
        }

        if (error instanceof DomainError) {
            return sendError(res, error.status, error.message);
        }

        const clientErrorStatus = readClientErrorStatus(error);
        if (clientErrorStatus !== null) {
            // Erro do cliente, não falha do servidor: registra sem stack.
            logger.warn(
                `Requisição inválida em ${req.method} ${req.originalUrl}: ${error.message}`
            );
            return sendError(res, clientErrorStatus, error.message);
        }

        logger.error(`Falha ao processar ${req.method} ${req.originalUrl}`, error);

        return sendError(res, INTERNAL_SERVER_ERROR, INTERNAL_ERROR_MESSAGE);
    };
}

/**
 * Status de erro de cliente que o middleware marcou como seguro de expor.
 *
 * `expose` é a convenção do `http-errors`, usada pelo `body-parser`: indica que
 * a mensagem descreve o problema do cliente e não vaza detalhe interno.
 */
function readClientErrorStatus(error) {
    const status = error?.status ?? error?.statusCode;

    const isExposableClientError =
        error?.expose === true &&
        Number.isInteger(status) &&
        status >= MIN_CLIENT_ERROR &&
        status <= MAX_CLIENT_ERROR;

    return isExposableClientError ? status : null;
}

module.exports = { createErrorHandler };
