'use strict';

const express = require('express');

const { createContainer } = require('./container');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createRoutes } = require('./routes');

const API_PREFIX = '/api';

/**
 * Montagem da aplicação Express.
 *
 * Recebe conexão, configuração e logger já prontos em vez de criá-los — é o que
 * permite subir a app contra um banco de teste sem tocar em `server.js`. O
 * `AppManager` original abria a conexão SQLite no construtor, então não havia
 * como instanciá-lo sem banco.
 *
 * A ordem do pipeline importa: parser de corpo, rotas e, por último, o error
 * handler, que precisa ser o último `use` para receber o que as rotas
 * propagarem.
 */
function createApp({ db, settings, logger }) {
    const app = express();

    // Não anunciar o framework e a versão em toda resposta.
    app.disable('x-powered-by');

    app.use(express.json());
    app.use(API_PREFIX, createRoutes(createContainer({ db, settings, logger })));
    app.use(createErrorHandler(logger));

    return app;
}

module.exports = { createApp };
