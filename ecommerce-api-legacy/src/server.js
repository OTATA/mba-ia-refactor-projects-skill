'use strict';

const { createApp } = require('./app');
const { loadSettings } = require('./config/settings');
const { createConnection } = require('./infrastructure/database');
const { createLogger } = require('./infrastructure/logger');
const { createSchema } = require('./infrastructure/schema');
const { seedDatabase } = require('./infrastructure/seeds');
const { createPasswordHasher } = require('./container');

const SHUTDOWN_SIGNALS = ['SIGINT', 'SIGTERM'];
const EXIT_FAILURE = 1;

/**
 * Entry point.
 *
 * Ordem explícita do boot — configuração, conexão, schema, seeds, aplicação,
 * escuta — no lugar do `manager.initDb(); manager.setupRoutes(app)` que
 * escondia DDL, seeds e registro de rotas atrás de dois métodos de um God
 * Object.
 *
 * Falha de boot derruba o processo com código de erro em vez de subir uma
 * aplicação meio inicializada: no original, erro de DDL era ignorado e a API
 * atendia requisições com schema incompleto.
 */
async function main() {
    const logger = createLogger();
    const settings = loadSettings();
    const db = createConnection(settings);

    createSchema(db);

    if (settings.seedDatabase) {
        await seedDatabase({ db, passwordHasher: createPasswordHasher(), logger });
    }

    const app = createApp({ db, settings, logger });
    const server = app.listen(settings.port, () => {
        logger.info(
            `LMS API rodando na porta ${settings.port} (${settings.nodeEnv})`
        );
    });

    registerShutdown({ server, db, logger });
    registerCrashGuards(logger);
}

/** Fecha servidor e conexão para não deixar o arquivo do banco meio escrito. */
function registerShutdown({ server, db, logger }) {
    let shuttingDown = false;

    for (const signal of SHUTDOWN_SIGNALS) {
        process.on(signal, () => {
            if (shuttingDown) return;
            shuttingDown = true;

            logger.info(`Recebido ${signal}, encerrando...`);
            server.close(() => {
                db.close();
                logger.info('Encerrado.');
            });
        });
    }
}

/**
 * Rede de segurança para falhas que escapam do pipeline do Express.
 *
 * O original não tinha nada disso: o TypeError de `cc.startsWith` num payload
 * malformado subia como `uncaughtException` e matava o processo sem log algum.
 * Isso agora é tratado na validação, mas o guarda fica para que qualquer falha
 * futura fora do ciclo de requisição deixe rastro antes de encerrar.
 */
function registerCrashGuards(logger) {
    process.on('unhandledRejection', (reason) => {
        logger.error('Promise rejeitada sem tratamento', reason);
    });

    process.on('uncaughtException', (error) => {
        logger.error('Exceção não capturada, encerrando processo', error);
        process.exit(EXIT_FAILURE);
    });
}

main().catch((error) => {
    // Sem logger garantido neste ponto: a falha pode ser da própria configuração.
    console.error('[ERROR] Falha ao iniciar a aplicação', error);
    process.exit(EXIT_FAILURE);
});
