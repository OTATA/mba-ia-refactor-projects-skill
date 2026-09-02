'use strict';

const { Router } = require('express');

/**
 * Mapa de rotas da API.
 *
 * Substitui `AppManager.setupRoutes`, um método de 114 linhas que registrava as
 * três rotas e embutia a implementação inteira de cada uma. Aqui só existe o
 * mapeamento caminho → controller; dá para ler a superfície da API de uma vez.
 *
 * Os três caminhos são idênticos aos originais (montados sob `/api` em
 * `src/app.js`). Nenhum deles usa sintaxe de rota afetada pelas mudanças de
 * path matching do Express 5.
 */
function createRoutes({
    checkoutController,
    financialReportController,
    userController,
}) {
    const router = Router();

    router.post('/checkout', checkoutController.handle);
    router.get('/admin/financial-report', financialReportController.handle);
    router.delete('/users/:id', userController.remove);

    return router;
}

module.exports = { createRoutes };
