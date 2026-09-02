'use strict';

const { FinancialReport } = require('../models/financialReport');

/**
 * Geração do relatório financeiro.
 *
 * Fica fino de propósito: a leitura está no repositório e a agregação — quais
 * pagamentos somam receita, como tratar matrícula órfã — está no modelo
 * `FinancialReport`, onde pode ser testada sem banco e sem HTTP.
 */
class FinancialReportService {
    #reports;

    constructor(financialReportRepository) {
        this.#reports = financialReportRepository;
    }

    generate() {
        return FinancialReport.fromRows(this.#reports.findReportRows());
    }
}

module.exports = { FinancialReportService };
