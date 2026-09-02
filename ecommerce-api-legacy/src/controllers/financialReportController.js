'use strict';

const { financialReport } = require('../views/responses');

/**
 * `GET /api/admin/financial-report`.
 *
 * ATENÇÃO — débito de segurança registrado na auditoria: este endpoint não
 * exige autenticação e devolve nome de todos os alunos e valores pagos
 * individualmente. Continua aberto porque adicionar autenticação seria
 * comportamento novo, fora do escopo desta refatoração. Não deve ir a produção
 * assim: falta um middleware de autenticação e checagem de papel `admin`.
 */
class FinancialReportController {
    #financialReportService;

    constructor(financialReportService) {
        this.#financialReportService = financialReportService;
    }

    handle = (req, res) => {
        const report = this.#financialReportService.generate();

        res.json(financialReport(report));
    };
}

module.exports = { FinancialReportController };
