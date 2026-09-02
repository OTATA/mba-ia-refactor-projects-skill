'use strict';

const { randomBytes, scrypt, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');

const scryptAsync = promisify(scrypt);

/**
 * Derivação de senha com scrypt.
 *
 * Substitui `badCrypto` de `src/utils.js`, que não era uma função de hash. O
 * laço concatenava 10.000 vezes o MESMO par de caracteres do Base64 da senha e
 * truncava o resultado em 10, então o valor final era aquele par repetido cinco
 * vezes: dependia apenas dos primeiros bytes da senha, sem salt, determinístico
 * e reversível por Base64. As 10.000 iterações não agregavam segurança alguma —
 * eram CPU desperdiçada de forma síncrona, bloqueando o event loop.
 *
 * scrypt vem do `node:crypto`, então não adiciona dependência, e é usado na
 * forma assíncrona justamente para não bloquear o event loop na derivação.
 *
 * O hash é armazenado num formato autodescritivo — `scrypt$1$N$r$p$salt$key` —
 * para que os parâmetros de custo possam subir no futuro sem invalidar os
 * hashes já gravados.
 */

const FORMAT_TAG = 'scrypt';
const FORMAT_VERSION = '1';
const FIELD_SEPARATOR = '$';
const SALT_BYTES = 16;
const KEY_BYTES = 64;

// 2**14 mantém o consumo de memória (128 * N * r ≈ 16 MiB) abaixo do `maxmem`
// default do Node, mas `maxmem` é declarado explicitamente para que subir o
// custo mais tarde não estoure o limite em silêncio.
const COST = 2 ** 14;
const BLOCK_SIZE = 8;
const PARALLELIZATION = 1;
const MAX_MEMORY = 64 * 1024 * 1024;

class PasswordHasher {
    async hash(plainPassword) {
        assertPassword(plainPassword);

        const salt = randomBytes(SALT_BYTES);
        const derivedKey = await derive(plainPassword, salt, {
            cost: COST,
            blockSize: BLOCK_SIZE,
            parallelization: PARALLELIZATION,
        });

        return [
            FORMAT_TAG,
            FORMAT_VERSION,
            COST,
            BLOCK_SIZE,
            PARALLELIZATION,
            salt.toString('hex'),
            derivedKey.toString('hex'),
        ].join(FIELD_SEPARATOR);
    }

    /**
     * Contraparte de `hash`, usada na comparação em tempo constante.
     *
     * Ainda não há endpoint de login — a auditoria registrou a ausência de
     * autenticação como débito bloqueante para produção —, mas um hash sem
     * caminho de verificação não tem como ser conferido, e é aqui que a
     * comparação precisa acontecer para não vazar informação por tempo.
     */
    async verify(plainPassword, storedHash) {
        if (typeof plainPassword !== 'string' || typeof storedHash !== 'string') {
            return false;
        }

        const parts = storedHash.split(FIELD_SEPARATOR);
        const [tag, version, cost, blockSize, parallelization, salt, key] = parts;

        if (parts.length !== 7 || tag !== FORMAT_TAG || version !== FORMAT_VERSION) {
            return false;
        }

        const expectedKey = Buffer.from(key, 'hex');
        const derivedKey = await derive(plainPassword, Buffer.from(salt, 'hex'), {
            cost: Number(cost),
            blockSize: Number(blockSize),
            parallelization: Number(parallelization),
            keyLength: expectedKey.length,
        });

        return timingSafeEqual(derivedKey, expectedKey);
    }
}

function assertPassword(plainPassword) {
    if (typeof plainPassword !== 'string' || plainPassword.length === 0) {
        throw new TypeError('A senha a ser derivada precisa ser uma string não vazia');
    }
}

function derive(plainPassword, salt, { cost, blockSize, parallelization, keyLength }) {
    return scryptAsync(plainPassword, salt, keyLength ?? KEY_BYTES, {
        N: cost,
        r: blockSize,
        p: parallelization,
        maxmem: MAX_MEMORY,
    });
}

module.exports = { PasswordHasher };
