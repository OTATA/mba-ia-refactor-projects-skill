'use strict';

const { CheckoutController } = require('./controllers/checkoutController');
const {
    FinancialReportController,
} = require('./controllers/financialReportController');
const { UserController } = require('./controllers/userController');
const { AuditLogRepository } = require('./repositories/auditLogRepository');
const { CourseRepository } = require('./repositories/courseRepository');
const { EnrollmentRepository } = require('./repositories/enrollmentRepository');
const {
    FinancialReportRepository,
} = require('./repositories/financialReportRepository');
const { PaymentRepository } = require('./repositories/paymentRepository');
const { UserRepository } = require('./repositories/userRepository');
const { CheckoutService } = require('./services/checkoutService');
const {
    FinancialReportService,
} = require('./services/financialReportService');
const { PaymentGateway } = require('./services/paymentGateway');
const { PasswordHasher } = require('./services/passwordHasher');
const { UserService } = require('./services/userService');

/**
 * Composição das dependências.
 *
 * Único lugar do projeto que sabe montar o grafo de objetos. Cada camada recebe
 * suas dependências pelo construtor e não instancia as de baixo — é isso que
 * permite testar serviço com repositório falso e controller com serviço falso,
 * algo impossível no `AppManager`, que criava a conexão SQLite no próprio
 * construtor e amarrava tudo junto.
 *
 * A direção das dependências é sempre a mesma:
 * controller → service → repository → banco.
 */

function createPasswordHasher() {
    return new PasswordHasher();
}

function createContainer({ db, settings, logger }) {
    const userRepository = new UserRepository(db);
    const courseRepository = new CourseRepository(db);
    const enrollmentRepository = new EnrollmentRepository(db);
    const paymentRepository = new PaymentRepository(db);
    const auditLogRepository = new AuditLogRepository(db);
    const financialReportRepository = new FinancialReportRepository(db);

    const passwordHasher = createPasswordHasher();
    const paymentGateway = new PaymentGateway({
        apiKey: settings.paymentGatewayKey,
        logger,
    });

    const checkoutService = new CheckoutService({
        db,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        passwordHasher,
        paymentGateway,
    });
    const financialReportService = new FinancialReportService(
        financialReportRepository
    );
    const userService = new UserService(userRepository);

    return {
        checkoutController: new CheckoutController(checkoutService),
        financialReportController: new FinancialReportController(
            financialReportService
        ),
        userController: new UserController(userService),
    };
}

module.exports = { createContainer, createPasswordHasher };
