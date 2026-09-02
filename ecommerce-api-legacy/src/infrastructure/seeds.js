'use strict';

/**
 * Dados de demonstração.
 *
 * Mesmos registros do `AppManager.initDb` — usuário, dois cursos, uma matrícula
 * e o pagamento correspondente — com duas diferenças:
 *
 *  - a senha do usuário passa pelo hasher. O original gravava `'123'` em texto
 *    plano direto na coluna `pass`, sem passar sequer pelo `badCrypto`, o que
 *    deixava a coluna com dois formatos incompatíveis;
 *  - a carga é idempotente. O original rodava a cada boot, o que só não
 *    duplicava dados porque o banco era sempre em memória; com `DATABASE_PATH`
 *    apontando para arquivo, rodaria de novo em cima da base existente.
 */

const SEED_USER = {
    name: 'Leonan',
    email: 'leonan@fullcycle.com.br',
    password: '123',
};

const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0, active: 1 },
    { title: 'Docker', price: 497.0, active: 1 },
];

const SEED_PAYMENT_STATUS = 'PAID';

async function seedDatabase({ db, passwordHasher, logger }) {
    const { total } = db.prepare('SELECT COUNT(*) AS total FROM users').get();

    if (total > 0) {
        logger.info('Seeds ignoradas: banco já contém dados.');
        return false;
    }

    // Derivação é assíncrona de propósito (não bloquear o event loop), então
    // acontece fora da transação — `db.transaction()` exige callback síncrono.
    const passwordHash = await passwordHasher.hash(SEED_USER.password);

    const insertSeeds = db.transaction(() => {
        const { lastInsertRowid: userId } = db
            .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
            .run(SEED_USER.name, SEED_USER.email, passwordHash);

        const insertCourse = db.prepare(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)'
        );
        const courseIds = SEED_COURSES.map(
            (course) =>
                insertCourse.run(course.title, course.price, course.active)
                    .lastInsertRowid
        );

        const { lastInsertRowid: enrollmentId } = db
            .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
            .run(userId, courseIds[0]);

        db.prepare(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)'
        ).run(enrollmentId, SEED_COURSES[0].price, SEED_PAYMENT_STATUS);
    });

    insertSeeds();
    logger.info('Seeds carregadas.');
    return true;
}

module.exports = { seedDatabase };
