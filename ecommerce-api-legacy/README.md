# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, usada como entrada do desafio
`refactor-arch`. Este diretório contém o resultado da refatoração: o monólito de
3 arquivos foi reorganizado em camadas, sem alteração das regras de negócio.

O relatório completo da auditoria está em [`../reports/ecommerce-api-legacy.md`](../reports/ecommerce-api-legacy.md).

## Requisitos

Node.js >= 22 (exigido pelo `better-sqlite3` 13).

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória por
default e carrega seeds automaticamente no boot.

Para rodar com configuração de arquivo:

```bash
cp .env.example .env
npm run start:env
```

Exemplos de requisições estão em `api.http`.

## Configuração

Toda configuração vem do ambiente — ver `.env.example`. Antes, `src/utils.js`
versionava senha de banco e a chave de produção do gateway (`pk_live_...`) no
repositório.

| Variável | Default | Descrição |
| --- | --- | --- |
| `NODE_ENV` | `development` | `production` torna `PAYMENT_GATEWAY_KEY` obrigatória |
| `PORT` | `3000` | Porta HTTP |
| `DATABASE_PATH` | `:memory:` | Caminho do arquivo SQLite |
| `SEED_DATABASE` | ligado fora de produção | Carga de dados de demonstração |
| `SQL_DEBUG` | `false` | Loga cada query |
| `PAYMENT_GATEWAY_KEY` | placeholder de dev | Chave do gateway |

## Estrutura

```
src/
├── server.js                 entry point: boot, escuta, shutdown
├── app.js                     montagem do Express (pipeline)
├── container.js               composição das dependências
├── errors.js                  erros de domínio (sem HTTP)
├── config/
│   └── settings.js            configuração lida do ambiente
├── infrastructure/
│   ├── database.js            conexão SQLite (foreign_keys, WAL)
│   ├── schema.js              DDL, foreign keys, índices
│   ├── seeds.js               dados de demonstração (idempotentes)
│   └── logger.js              saída de log
├── models/
│   ├── course.js              entidade Curso
│   ├── paymentStatus.js       PAID / DENIED
│   └── financialReport.js     agregação do relatório
├── repositories/              todo o SQL vive aqui
│   ├── userRepository.js
│   ├── courseRepository.js
│   ├── enrollmentRepository.js
│   ├── paymentRepository.js
│   ├── auditLogRepository.js
│   └── financialReportRepository.js
├── services/                  regras de negócio
│   ├── checkoutService.js
│   ├── financialReportService.js
│   ├── userService.js
│   ├── passwordHasher.js      scrypt
│   └── paymentGateway.js      simulação de cobrança
├── controllers/               fronteira HTTP (finos)
│   ├── checkoutController.js
│   ├── financialReportController.js
│   └── userController.js
├── validators/
│   └── checkoutValidator.js   validação do payload
├── views/
│   └── responses.js           formato das respostas
├── middlewares/
│   └── errorHandler.js        tratamento central de erros
└── routes/
    └── index.js               mapa caminho → controller
```

Direção das dependências: `controller → service → repository → banco`.
Nenhuma camada abaixo dos controllers conhece `req`/`res`.

## Endpoints

Os três endpoints e seus contratos foram preservados.

| Método | Caminho | Resposta |
| --- | --- | --- |
| `POST` | `/api/checkout` | `200 { "msg": "Sucesso", "enrollment_id": n }` |
| `GET` | `/api/admin/financial-report` | `200 [{ "course", "revenue", "students": [{ "student", "paid" }] }]` |
| `DELETE` | `/api/users/:id` | `200` texto |

Campos do payload de checkout (`usr`, `eml`, `pwd`, `c_id`, `card`) são o
contrato público e foram mantidos como estavam.

## Débitos conhecidos

Registrados na auditoria e **deliberadamente fora do escopo** da refatoração,
porque exigiriam adicionar comportamento novo:

- **Sem autenticação.** `GET /api/admin/financial-report` expõe nome de todos os
  alunos e valores pagos a qualquer requisição anônima, e `DELETE /api/users/:id`
  permite apagar qualquer usuário. Não deve ir a produção assim.
- **Senha default `123456`** quando `pwd` não é informado no checkout — regra de
  negócio existente, preservada.
- **Sem testes automatizados.** As candidatas óbvias são `CheckoutService` e
  `FinancialReport.fromRows`, ambas agora testáveis sem HTTP e sem banco.
- **Chave do gateway exposta no histórico do Git** precisa ser rotacionada no
  provedor.
