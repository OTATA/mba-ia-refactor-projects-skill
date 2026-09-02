'use strict';

/**
 * Configuração da aplicação, lida do ambiente.
 *
 * Substitui o objeto `config` hardcoded em `src/utils.js`, que versionava no
 * repositório a senha do banco e a chave de produção do gateway de pagamento
 * (`pk_live_...`). Segredo em código-fonte não pode ser rotacionado sem rewrite
 * de histórico e vaza para qualquer pessoa com acesso de leitura ao repositório.
 *
 * `dbUser`, `dbPass` e `smtpUser` foram removidos: nenhum dos três era lido em
 * lugar algum do código, e SQLite não tem autenticação — não havia o que
 * configurar.
 *
 * Em produção a chave do gateway é obrigatória e o boot falha sem ela: é melhor
 * não subir do que subir sem credencial de cobrança. Fora de produção existe um
 * placeholder explicitamente não-secreto para não atrapalhar o dev local.
 */

const DEFAULT_PORT = 3000;
const IN_MEMORY_DATABASE = ':memory:';
const DEVELOPMENT_PAYMENT_GATEWAY_KEY = 'pk_test_local_dev_only';
const MIN_PORT = 1;
const MAX_PORT = 65535;
const TRUTHY_VALUES = ['1', 'true', 'yes', 'on'];

class ConfigurationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ConfigurationError';
    }
}

function parsePort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;

    const port = Number(raw);
    if (!Number.isInteger(port) || port < MIN_PORT || port > MAX_PORT) {
        throw new ConfigurationError(`PORT inválida: "${raw}"`);
    }
    return port;
}

function parseBoolean(raw, fallback) {
    if (raw === undefined || raw === '') return fallback;
    return TRUTHY_VALUES.includes(String(raw).toLowerCase());
}

function loadSettings(env = process.env) {
    const nodeEnv = env.NODE_ENV ?? 'development';
    const isProduction = nodeEnv === 'production';

    if (isProduction && !env.PAYMENT_GATEWAY_KEY) {
        throw new ConfigurationError(
            'PAYMENT_GATEWAY_KEY é obrigatória quando NODE_ENV=production'
        );
    }

    return Object.freeze({
        nodeEnv,
        isProduction,
        port: parsePort(env.PORT),
        // `:memory:` continua sendo o default para preservar o comportamento de
        // desenvolvimento descrito no README, mas agora é configurável — antes
        // estava fixo no construtor do `AppManager`, o que descartava todos os
        // dados a cada restart sem qualquer alternativa.
        databasePath: env.DATABASE_PATH ?? IN_MEMORY_DATABASE,
        seedDatabase: parseBoolean(env.SEED_DATABASE, !isProduction),
        // O `sqlite3.verbose()` original estava sempre ligado, inclusive em
        // produção, pagando captura de stack trace em toda operação de banco.
        sqlDebug: parseBoolean(env.SQL_DEBUG, false),
        paymentGatewayKey:
            env.PAYMENT_GATEWAY_KEY ?? DEVELOPMENT_PAYMENT_GATEWAY_KEY,
    });
}

module.exports = {
    loadSettings,
    ConfigurationError,
    IN_MEMORY_DATABASE,
};
