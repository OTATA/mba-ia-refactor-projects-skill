'use strict';

const { NotFoundError, PaymentDeclinedError } = require('../errors');
const { isApproved } = require('../models/paymentStatus');

const COURSE_NOT_FOUND_MESSAGE = 'Curso não encontrado';
const PAYMENT_DECLINED_MESSAGE = 'Pagamento recusado';

// Preserva o `p || "123456"` do código original. A auditoria registrou o
// default silencioso como falha de segurança, mas é regra de negócio existente
// e não foi alterada aqui.
const DEFAULT_PASSWORD = '123456';

/**
 * Fluxo de checkout.
 *
 * Regras preservadas do código original, sem qualquer alteração:
 *
 *  - só curso com `active = 1` pode ser comprado (404 'Curso não encontrado');
 *  - usuário inexistente para o e-mail informado é criado no ato;
 *  - senha ausente ou vazia usa o default '123456';
 *  - o usuário é criado ANTES da decisão do pagamento e permanece criado mesmo
 *    quando o pagamento é recusado — por isso a criação fica fora da transação
 *    de matrícula, e não por descuido;
 *  - cartão recusado responde 400 'Pagamento recusado';
 *  - o preço cobrado é o do curso no banco, não o informado na requisição.
 *
 * O que mudou: matrícula, pagamento e log de auditoria agora gravam numa única
 * transação. No original eram três `INSERT` em autocommit encadeados por
 * callback — se o insert de pagamento falhasse, a matrícula já estava
 * persistida e o cliente recebia 500, deixando aluno matriculado sem pagamento
 * registrado, que o relatório financeiro passava a contar com `paid: 0`.
 */
class CheckoutService {
    #db;
    #users;
    #courses;
    #enrollments;
    #payments;
    #auditLogs;
    #passwordHasher;
    #paymentGateway;

    constructor({
        db,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        passwordHasher,
        paymentGateway,
    }) {
        this.#db = db;
        this.#users = userRepository;
        this.#courses = courseRepository;
        this.#enrollments = enrollmentRepository;
        this.#payments = paymentRepository;
        this.#auditLogs = auditLogRepository;
        this.#passwordHasher = passwordHasher;
        this.#paymentGateway = paymentGateway;
    }

    async checkout({ name, email, courseId, cardNumber, password }) {
        const course = this.#courses.findPurchasableById(courseId);
        if (!course) {
            throw new NotFoundError(COURSE_NOT_FOUND_MESSAGE);
        }

        const userId = await this.#findOrCreateUser({ name, email, password });

        const status = this.#paymentGateway.charge({
            cardNumber,
            amount: course.price,
        });

        if (!isApproved(status)) {
            throw new PaymentDeclinedError(PAYMENT_DECLINED_MESSAGE);
        }

        return { enrollmentId: this.#enroll({ userId, course, status }) };
    }

    async #findOrCreateUser({ name, email, password }) {
        const existingUserId = this.#users.findIdByEmail(email);
        if (existingUserId !== null) {
            return existingUserId;
        }

        const passwordHash = await this.#passwordHasher.hash(
            password || DEFAULT_PASSWORD
        );

        return this.#users.create({ name, email, passwordHash });
    }

    /**
     * Matrícula, pagamento e auditoria numa transação só: ou os três gravam, ou
     * nenhum grava. `db.transaction()` exige callback síncrono, o que o driver
     * `better-sqlite3` garante.
     */
    #enroll({ userId, course, status }) {
        const persist = this.#db.transaction(() => {
            const enrollmentId = this.#enrollments.create({
                userId,
                courseId: course.id,
            });

            this.#payments.create({
                enrollmentId,
                amount: course.price,
                status,
            });

            this.#auditLogs.record(`Checkout curso ${course.id} por ${userId}`);

            return enrollmentId;
        });

        return persist();
    }
}

module.exports = { CheckoutService };
