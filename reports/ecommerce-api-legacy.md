# ARCHITECTURE AUDIT REPORT — ecommerce-api-legacy

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js, CommonJS) + Express 4.18.2 + sqlite3 5.1.6
Files:   3 analyzed | ~180 lines of code
Domain:  LMS / plataforma de cursos com fluxo de checkout
         (users, courses, enrollments, payments, audit_logs)

Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 6
================================
```

Data da auditoria: 2026-09-02

---

## Findings

### [CRITICAL] Exposed Credentials — segredos hardcoded e versionados

**File:** `src/utils.js:1-7`

```js
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

**Description:** Senha de banco, chave do gateway de pagamento (prefixo `pk_live_`, indicando
ambiente de produção) e usuário SMTP estão em texto plano no código-fonte e comitados no Git.

**Impact:** Qualquer pessoa com acesso ao repositório (ou ao histórico, mesmo após remoção)
obtém credenciais de produção. Rotação exige rewrite de histórico. Impossível ter configuração
distinta por ambiente.

**Recommendation:** Mover para variáveis de ambiente (`process.env`) com carregamento
centralizado e validação de presença no boot (fail-fast). `.env` já está no `.gitignore`.
Prover `.env.example` sem valores reais. **As chaves expostas devem ser rotacionadas** — o
`.gitignore` não remove o que já está no histórico.

---

### [CRITICAL] Sensitive Data Exposure — número de cartão e chave do gateway em log

**File:** `src/AppManager.js:45`

```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Description:** O PAN completo do cartão de crédito e a chave secreta do gateway são escritos
em stdout a cada checkout.

**Impact:** Violação direta de PCI-DSS (armazenamento de PAN em claro). Logs normalmente são
agregados, replicados e retidos em sistemas de terceiros, ampliando a superfície de vazamento.

**Recommendation:** Nunca logar dados de cartão nem segredos. Se rastreabilidade for
necessária, logar apenas os 4 últimos dígitos e um identificador de transação.

---

### [CRITICAL] Broken Cryptography — `badCrypto` não é uma função de hash

**File:** `src/utils.js:17-23`

```js
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

**Description:** O loop concatena 10.000 vezes **o mesmo** par de caracteres e depois trunca em
10 caracteres — ou seja, o resultado é aquele par repetido 5 vezes. O valor final depende apenas
dos ~1,5 primeiros bytes da senha. Não há salt, não há função de derivação, e a operação é
determinística e trivialmente reversível (é Base64).

**Impact:** Todas as senhas colapsam num espaço de algumas centenas de valores; senhas distintas
com o mesmo início produzem o mesmo "hash". Comprometimento total da autenticação. O custo de
10.000 iterações não agrega segurança alguma — é apenas CPU desperdiçada de forma síncrona,
bloqueando o event loop.

**Related:** `src/AppManager.js:18` — seed insere senha `'123'` em texto plano, sem passar
sequer por `badCrypto`, deixando o formato da coluna `pass` inconsistente.

**Recommendation:** Substituir por uma KDF reconhecida — `node:crypto.scrypt` (nativo, sem
dependência nova) ou `argon2`/`bcrypt`, sempre na variante assíncrona, com salt por usuário.

---

### [CRITICAL] God Object — `AppManager` acumula todas as responsabilidades

**File:** `src/AppManager.js:4-141`

**Description:** Uma única classe concentra: abertura da conexão SQLite (`:7`), DDL do schema
(`:12-16`), seeds (`:18-21`), registro de rotas HTTP (`:28`, `:80`, `:131`), parsing e validação
de request (`:29-35`), regra de negócio de checkout (`:43-64`), simulação do gateway de pagamento
(`:46`), persistência (`:50-57`), auditoria (`:57`), cache (`:59`) e agregação do relatório
financeiro (`:81-128`).

**Impact:** Nenhuma unidade é testável em isolamento — não há como testar a regra de aprovação de
pagamento sem subir Express e SQLite. Qualquer alteração toca o mesmo arquivo, maximizando
conflito de merge e risco de regressão. O nome `AppManager` não comunica responsabilidade alguma.

**Recommendation:** Separar em camadas: `config`, `infrastructure` (conexão + schema + seeds),
`repositories` (SQL), `services` (regra de negócio), `controllers` (HTTP), `routes`, com um
container de composição. Espelhar a estrutura já adotada no `code-smells-project` deste mesmo
repositório.

---

### [CRITICAL] Missing Authentication/Authorization em endpoints admin e destrutivos

**File:** `src/AppManager.js:80` e `src/AppManager.js:131`

**Description:** `GET /api/admin/financial-report` e `DELETE /api/users/:id` não exigem qualquer
credencial. O relatório retorna nome de todos os alunos, receita por curso e valores pagos
individualmente.

**Impact:** Exposição anônima de dados pessoais e financeiros de toda a base (LGPD). O endpoint
de exclusão permite que qualquer requisição não autenticada apague qualquer usuário — inclusive
em massa, iterando IDs.

**Recommendation:** Middleware de autenticação, mais checagem de papel (`admin`) nas rotas
administrativas. Fora do escopo de refatoração pura (adiciona comportamento novo), mas deve ser
registrado como débito bloqueante para produção.

---

### [HIGH] Controller with Direct Database Access — SQL cru dentro dos handlers HTTP

**File:** `src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133`

**Description:** Todas as 11 queries do sistema estão escritas inline dentro de callbacks de rota
Express, misturando protocolo HTTP (`res.status().send()`) com acesso a dados no mesmo bloco.

**Impact:** A regra de negócio fica acoplada tanto ao Express quanto ao dialeto SQLite. Trocar de
banco, adicionar cache ou testar a lógica exige mock de `req`/`res`. Queries duplicadas não são
reaproveitáveis.

**Recommendation:** Extrair para repositórios por agregado (`UserRepository`,
`CourseRepository`, `EnrollmentRepository`, `PaymentRepository`, `AuditLogRepository`) expondo
métodos de domínio e devolvendo Promises.

*Nota:* as queries usam parâmetros posicionais (`?`) corretamente — **não há SQL Injection**.

---

### [HIGH] Missing Transaction — checkout multi-etapa sem atomicidade

**File:** `src/AppManager.js:50-63` (e `:69-72`)

**Description:** O checkout executa quatro escritas independentes em autocommit: criação do
usuário, `INSERT` em `enrollments`, `INSERT` em `payments` e `INSERT` em `audit_logs`. Não existe
`BEGIN`/`COMMIT`/`ROLLBACK`.

**Impact:** Falha parcial deixa o banco inconsistente. Se o insert de `payments` falhar
(`:55`), a matrícula **já foi persistida** e o cliente recebe 500 — o aluno fica matriculado sem
pagamento registrado, e o relatório financeiro passa a contá-lo com `paid: 0`. Não há compensação.

**Recommendation:** Envolver a operação numa transação única no nível do serviço, com rollback em
qualquer falha. Como o `sqlite3` serializa por conexão, isso é seguro com uma conexão dedicada.

---

### [HIGH] Missing Referential Integrity — registros órfãos por design

**File:** `src/AppManager.js:12-16` (schema) e `src/AppManager.js:131-137` (delete)

```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```

**Description:** Nenhuma tabela declara `FOREIGN KEY`, e o `PRAGMA foreign_keys` do SQLite não é
habilitado (vem desligado por padrão). O `DELETE` de usuário não trata dependentes — a própria
mensagem de resposta admite o vazamento.

**Impact:** `enrollments` e `payments` apontam para `user_id` inexistente. O relatório financeiro
(`:113`) já compensa isso com `'Unknown'`, evidenciando corrupção acumulada. Receita passa a
incluir pagamentos de usuários deletados.

**Recommendation:** Declarar as FKs no schema, habilitar `PRAGMA foreign_keys = ON` na abertura da
conexão e decidir explicitamente a política (`ON DELETE RESTRICT` ou remoção em cascata dentro de
transação). Manter o comportamento observável atual, mas parar de gerar novos órfãos.

---

### [HIGH] Error Swallowing — erros de callback ignorados

**File:** `src/AppManager.js:57, 92-93, 104, 106, 133` e `src/AppManager.js:11-22`

**Description:**
- `:57` — erro do insert de auditoria é recebido e descartado; responde `200 Sucesso` de todo modo.
- `:92-93` — `err` é ignorado e `enrollments.length` é acessado na linha seguinte; se a query
  falhar, `enrollments` é `undefined` → `TypeError`.
- `:104, :106` — erros de usuário e pagamento silenciosamente ignorados.
- `:133` — erro do `DELETE` ignorado; sempre responde sucesso.
- `:11-22` — nenhum `run` do `initDb` verifica erro; falha de DDL passa despercebida e a aplicação
  sobe com schema incompleto.

**Impact:** Falhas silenciosas. O cliente recebe confirmação de operações que não aconteceram.
Diagnóstico em produção fica inviável — não há log de erro em nenhum desses caminhos.

**Recommendation:** Promisificar o acesso ao banco, propagar erros por `throw` e centralizar o
tratamento num middleware de erro do Express, com logging estruturado.

---

### [HIGH] Unhandled Exception — crash do processo por input não validado

**File:** `src/AppManager.js:46` (e `src/utils.js:20`)

```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

**Description:** A validação em `:35` checa apenas truthiness dos campos, não o tipo. Se `card`
vier como número no JSON (`"card": 4111222233334444`), `cc.startsWith` não existe → `TypeError`
lançado **dentro de um callback do sqlite3**, fora de qualquer bloco do Express.

**Impact:** Express não captura exceções em callbacks assíncronos: a exceção sobe como
`uncaughtException` e **derruba o processo inteiro**. Como o banco é `:memory:` (ver LOW), todos
os dados são perdidos junto. É uma negação de serviço acionável por um único request malformado.
`Buffer.from(pwd)` em `utils.js:20` tem o mesmo problema para `pwd` numérico.

**Recommendation:** Validação de schema de entrada (tipo + formato) antes de qualquer I/O,
retornando `400`. Adicionar handler de `uncaughtException`/`unhandledRejection` como rede de
segurança.

---

### [MEDIUM] N+1 Query — relatório financeiro

**File:** `src/AppManager.js:83-128`

**Description:** 1 query para listar cursos, + 1 query de matrículas por curso, + 2 queries
(usuário e pagamento) por matrícula. Com C cursos e E matrículas: `1 + C + 2E` queries.

**Impact:** Para 50 cursos e 5.000 matrículas: 10.051 queries por request. Latência cresce
linearmente com a base e o endpoint não tem paginação nem cache.

**Recommendation:** Uma única query com `JOIN` entre `courses`, `enrollments`, `users` e
`payments`, agregando em memória — ou `SUM` condicional em SQL. Preservar exatamente o formato
de saída atual.

---

### [MEDIUM] Callback Hell + contadores manuais de concorrência

**File:** `src/AppManager.js:37-77` e `src/AppManager.js:83-128`

**Description:** O checkout aninha 5 níveis de callback. O relatório usa contadores decrementais
escritos à mão (`coursesPending`, `enrPending`) para sincronizar N operações assíncronas.

**Impact:** Se qualquer callback interno lançar ou retornar cedo, o contador nunca chega a zero e
**a resposta nunca é enviada** — o request pendura até o timeout do cliente, mantendo o socket
aberto. A ordem de `report` (`:96`, `:119`) depende da ordem de conclusão das queries, portanto a
saída é **não determinística** entre chamadas idênticas. Complexidade ciclomática alta e fluxo de
erro impossível de seguir.

**Recommendation:** Converter para `async`/`await` sobre uma camada promisificada; usar
`Promise.all` onde o paralelismo for desejável. Elimina os contadores e torna o erro propagável.

---

### [MEDIUM] Long Function / God Method — `setupRoutes`

**File:** `src/AppManager.js:25-138`

**Description:** Um único método de 114 linhas registra três rotas e embute a implementação
completa das três.

**Impact:** Excede qualquer limite razoável de tamanho de função; impossível revisar ou testar
por partes.

**Recommendation:** Um controller por recurso + um módulo de rotas declarativo.

---

### [MEDIUM] Inconsistent HTTP Contract

**File:** `src/AppManager.js:35, 38, 48, 60, 135`

**Description:** Respostas de erro são `text/plain` em português (`"Bad Request"`, `"Erro DB"`,
`"Curso não encontrado"`) enquanto o sucesso é JSON (`:60`). Pagamento recusado retorna `400`
(`:48`), semanticamente incorreto — a requisição era válida. `DELETE` retorna `200` com texto.

**Impact:** Clientes não conseguem tratar erros programaticamente; é preciso comparar strings.
Mistura de formatos quebra parsers.

**Recommendation:** Envelope JSON único para erro (`{ error: { code, message } }`) via middleware.
Manter os status codes atuais para não quebrar o contrato existente, exceto onde o usuário
autorizar corrigir.

---

### [MEDIUM] Uso incorreto de `this` / `self` mesclados

**File:** `src/AppManager.js:26, 50, 52, 54, 57, 69, 71`

**Description:** `const self = this` (`:26`) coexiste com arrow functions que já preservam `this`.
Os callbacks de `run` usam `function(err)` deliberadamente para acessar `this.lastID` (`:52`,
`:71`), o que **rebinda `this`** — daí a necessidade de `self.db` em `:54` e `:57`.

**Impact:** Dentro de `:50-63`, `this` significa duas coisas diferentes em escopos adjacentes.
Trocar `function` por arrow "para modernizar" quebra `this.lastID` silenciosamente — armadilha
real de manutenção.

**Recommendation:** Encapsular em um helper promisificado que retorne `{ lastID, changes }`
explicitamente, eliminando a dependência do `this` dinâmico.

---

### [LOW] Poor Naming

**File:** `src/AppManager.js:29-33`, `src/utils.js`, nome da classe

**Description:** Variáveis de uma letra (`u`, `e`, `p`, `cid`, `cc`); campos de API abreviados
(`usr`, `eml`, `pwd`, `c_id`, `card`); `AppManager` não descreve responsabilidade; `utils.js` é
gaveta de entulho (config + log + cache + cripto + estado global).

**Recommendation:** Renomear identificadores internos livremente. **Os nomes dos campos do payload
(`usr`, `eml`, `pwd`, `c_id`, `card`) fazem parte do contrato público** documentado em `api.http`
e devem ser preservados na refatoração.

---

### [LOW] Magic Numbers e Magic Strings

**File:** `src/AppManager.js:46, 48, 68`, `src/utils.js:19, 22`

**Description:** `"4"` como prefixo que aprova o cartão (`:46`), `"123456"` como senha default
silenciosa (`:68`), `10000` e `10` em `badCrypto`, literais `'PAID'`/`'DENIED'`/`'active = 1'`
espalhados sem constante.

**Impact:** A regra "cartão que começa com 4 é aprovado" está escondida num ternário sem nome nem
comentário. Senha default `"123456"` atribuída silenciosamente é falha de segurança por si só.

**Recommendation:** Extrair constantes nomeadas e um `PaymentStatus` enumerado. Manter os valores
idênticos — a regra de negócio não muda.

---

### [LOW] Dead Code e Memory Leak

**File:** `src/utils.js:9-10, 14, 25` e `src/AppManager.js:2`

**Description:**
- `totalRevenue` (`utils.js:10`) é declarado, exportado e **nunca alterado**; por ser primitivo, é
  exportado por valor — permaneceria `0` mesmo se fosse mutado. Importado em `AppManager.js:2` e
  nunca usado.
- `globalCache` (`utils.js:9`) só recebe escrita (`:14`), nunca leitura. Cresce sem limite nem TTL
  a cada checkout.

**Impact:** Vazamento de memória lento e monotônico no processo. Código morto sugere
funcionalidade inexistente.

**Recommendation:** Remover `totalRevenue`, `globalCache` e `logAndCache` — nenhum tem leitor.

---

### [LOW] Banco em memória hardcoded

**File:** `src/AppManager.js:7`

**Description:** `new sqlite3.Database(':memory:')` sem possibilidade de configuração.

**Impact:** Todo o estado é perdido a cada restart ou crash (ver o finding de crash acima). Impede
qualquer uso além de demonstração.

**Recommendation:** Tornar o caminho configurável por env, mantendo `:memory:` como default para
não alterar o comportamento atual de desenvolvimento.

---

### [LOW] `sqlite3.verbose()` habilitado incondicionalmente

**File:** `src/AppManager.js:1`

**Description:** O modo verbose captura stack traces em toda operação de banco.

**Impact:** Custo de performance e ruído em log, sem condicional de ambiente.

**Recommendation:** Ativar apenas fora de produção.

---

### [LOW] Ausência de tooling de qualidade

**File:** `package.json:1-13`

**Description:** Sem `devDependencies`, sem framework de teste, sem linter/formatter, sem campo
`engines`, sem script de test. Zero cobertura de testes no projeto.

**Impact:** Nenhuma rede de segurança para refatorar; nenhuma garantia de versão de Node.

**Recommendation:** Declarar `engines`, adicionar testes ao menos para a regra de checkout e para
o agregado do relatório, que são a lógica de negócio de valor.

---

## Deprecated API / Dependency Report

Verificação conforme `api-depracated.md` — apenas fontes primárias (registry npm, documentação
oficial, changelogs e READMEs dos mantenedores). Consultado em 2026-09-02.

### 1. `sqlite3` — repositório oficialmente NÃO MANTIDO

| Campo | Valor |
|---|---|
| Pacote | `sqlite3` (TryGhost/node-sqlite3) |
| Versão no projeto | `^5.1.6` (`package.json:11`) |
| Última versão publicada | `6.0.1` (dist-tag `latest`) |
| Status | Repositório marcado como **unmaintained** |
| Substituto | `better-sqlite3`, ou `node:sqlite` (nativo) |
| Versão de remoção | Não aplicável — sem deprecação formal no npm |
| Fonte | README oficial do repositório; releases v6.0.0/v6.0.1 (2026-03-12) |

Citação verbatim do README oficial:

> **Note:** This repository is currently unmaintained. We will not update any of its issues or
> pull requests.

O changelog da v6.0.0 inclui a entrada *"Mark repository as unmaintained"*.

**Observação importante:** o pacote **não está formalmente deprecado** no registry npm — não há
campo `deprecated` nas versões 5.x. O risco é de manutenção e cadeia de suprimentos: a versão
`5.1.6` do projeto está duas releases atrás (`5.1.7` atualizou o SQLite embutido para v3.44.2 e
trocou o tooling de build para `prebuild`), e o histórico do pacote inclui uma CVE de execução de
código corrigida na `5.1.5`. Nenhuma correção futura de segurança é garantida.

**Nenhuma API deprecada do `sqlite3` é usada no código.** `Database`, `run`, `get`, `all`,
`serialize` e `verbose` são todos parte da API corrente.

### 2. `express` — 4.18.2 fora da linha suportada

| Campo | Valor |
|---|---|
| Pacote | `express` |
| Versão no projeto | `^4.18.2` (`package.json:10`) |
| Última versão publicada | `5.2.1` (dist-tag `latest`) |
| Status da linha 4.x | Suporte "ongoing", **mas apenas a última versão de cada linha major é suportada** |
| Substituto | `express@5` (requer Node.js ≥ 18) |
| Versão de remoção | Sem data de EOL publicada para a 4.x |
| Fonte | Página oficial de Version Support; guia oficial de migração para 5 |

A página oficial de suporte lista a linha 4.x iniciada em abril/2014 e a 5.x em setembro/2024,
ambas com término "ongoing", e declara explicitamente que *"only the latest version of any given
major release line is supported"*. `4.18.2` não é a última 4.x, logo está fora da janela de
suporte de segurança. A Express também firmou parceria com a HeroDevs para suporte estendido
comercial de versões legadas.

**Nenhuma API removida no Express 5 é usada por este código.** Verifiquei o guia oficial de
migração contra a base:

| API removida no Express 5 | Usada aqui? |
|---|---|
| `app.del()` | Não — usa `app.delete()` (`AppManager.js:131`) |
| `res.send(status, body)` / `res.send(status)` | Não — usa `res.status(n).send(...)` |
| `res.json(obj, status)` | Não — usa `res.status(n).json(...)` / `res.json(...)` |
| `req.param(name)` | Não — usa `req.params` / `req.body` |
| `res.sendfile()` | Não usado |
| `res.redirect('back')`, `express.static.mime` | Não usados |
| Padrões de rota com regex / wildcard não nomeado | Não — apenas `/api/users/:id` |

Ou seja, a migração para Express 5 é de baixo risco para este projeto. Deixo a decisão para o
usuário, pois é atualização de major e não refatoração de código.

### 3. Node.js core — nada deprecado em uso

- `Buffer.from()` (`utils.js:20`) é a forma **correta e atual**; o construtor deprecado
  `new Buffer()` não é usado.
- `require`/CommonJS não é deprecado.
- Nenhuma outra API core em uso figura na lista de deprecações do Node.

### 4. Alternativa nativa avaliada e não recomendada agora

`node:sqlite` foi avaliado como substituto do `sqlite3`. A documentação oficial do Node informa
`Stability: 1.2 — Release candidate` (adicionado em v22.5.0; deixou de exigir
`--experimental-sqlite` em v22.13.0/v23.4.0; promovido a release candidate em v25.7.0). Por ainda
não ser estável, **não recomendo** adotá-lo nesta refatoração.

---

## Restrição de escopo da refatoração

Os seguintes comportamentos são **regra de negócio** e devem ser preservados na Fase 3, mesmo
quando questionáveis:

1. Cartão que começa com `"4"` é aprovado; qualquer outro é recusado (`AppManager.js:46`).
2. Checkout cria o usuário automaticamente quando o e-mail não existe (`:66-72`).
3. Senha ausente usa o default `"123456"` (`:68`).
4. Apenas cursos com `active = 1` podem ser comprados (`:37`).
5. Apenas pagamentos com status `'PAID'` somam receita; o aluno aparece na lista independentemente
   do status (`:108-115`).
6. Usuário inexistente no relatório aparece como `'Unknown'` com `paid: 0` (`:113-114`).
7. Nomes dos campos do payload de checkout: `usr`, `eml`, `pwd`, `c_id`, `card`.
8. Status codes e formato do corpo de resposta das rotas existentes.

```
================================
Total: 21 findings
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 6
Deprecated dependencies: 2 (sqlite3 unmaintained, express 4.x fora de suporte)
Deprecated APIs in use: 0
================================
```

---

## Resolução (Fase 3)

| # | Finding | Situação |
|---|---|---|
| 1 | Credenciais hardcoded | Resolvido — `src/config/settings.js` lê do ambiente; `.env.example` criado. **A chave exposta ainda precisa ser rotacionada no provedor** |
| 2 | PAN e chave em log | Resolvido — `PaymentGateway` loga só os 4 últimos dígitos, nunca a chave |
| 3 | `badCrypto` | Resolvido — `PasswordHasher` com scrypt do `node:crypto`, salt por usuário, formato autodescritivo |
| 4 | God Object | Resolvido — 24 módulos em camadas; `controller → service → repository` |
| 5 | Sem autenticação | **Não resolvido, por escopo** — exigiria comportamento novo. Débito bloqueante registrado no README e nos controllers |
| 6 | SQL nos controllers | Resolvido — todo o SQL vive em `src/repositories/` |
| 7 | Checkout sem transação | Resolvido — matrícula + pagamento + auditoria em `db.transaction()`; rollback verificado |
| 8 | Órfãos / sem FK | Resolvido — FKs no schema, `PRAGMA foreign_keys = ON`, `ON DELETE CASCADE` |
| 9 | Erros engolidos | Resolvido — erro propaga por exceção até `middlewares/errorHandler.js` |
| 10 | Crash do processo | Resolvido — validação de tipo antes de qualquer I/O; guardas de processo em `server.js` |
| 11 | N+1 no relatório | Resolvido — `1 + C + 2E` queries viraram 1 |
| 12 | Callback hell | Resolvido — driver síncrono + `async/await`; contadores manuais eliminados |
| 13 | `setupRoutes` de 114 linhas | Resolvido — `routes/index.js` só mapeia caminho → controller |
| 14 | Contrato HTTP inconsistente | **Parcial, por escopo** — status codes e corpos preservados de propósito; centralizados em `views/responses.js` para migração futura |
| 15 | `this` / `self` mesclados | Resolvido — repositórios devolvem o id explicitamente |
| 16 | Nomes ruins | Resolvido internamente; `usr`/`eml`/`pwd`/`c_id`/`card` preservados (contrato público) |
| 17 | Magic numbers | Resolvido — constantes nomeadas; valores idênticos |
| 18 | Código morto / memory leak | Resolvido — `globalCache`, `logAndCache` e `totalRevenue` removidos |
| 19 | `:memory:` hardcoded | Resolvido — `DATABASE_PATH`, com `:memory:` como default |
| 20 | `verbose()` sempre ligado | Resolvido — `SQL_DEBUG`, default desligado |
| 21 | Sem tooling de qualidade | **Não resolvido** — `engines` declarado, mas o projeto segue sem testes e sem linter |

### Dependências

- `sqlite3` 5.1.6 → **`better-sqlite3` 13.0.3** (driver mantido; API síncrona habilita transação real)
- `express` 4.18.2 → **`express` 5.2.1** (`npm audit`: 0 vulnerabilidades)
- `package-lock.json` foi removido: pinava a árvore antiga e `npm ci` falharia contra o novo `package.json`. Regenerado por `npm install`.

### Dois defeitos encontrados durante a validação e corrigidos

1. **`pwd` de tipo não-string caía silenciosamente no default `'123456'`.** O validador tratava "ausente" e "tipo errado" como o mesmo caso, então `{"pwd": 123}` respondia 200 gravando a senha default — o cliente acreditaria ter definido uma senha. Passou a retornar 400.
2. **JSON malformado respondia 500 em vez de 400.** Tratar tudo que não fosse `DomainError` como erro interno engolia o status dos erros do `express.json()`, que o handler default do Express 4 respondia como 400. O error handler passou a respeitar erro de cliente marcado com `expose: true`.

### Validação executada

Node.js 22.20.0, `express` 5.2.1 e `better-sqlite3` 13.0.3 instalados; aplicação executada de fato.

- Boot limpo em development e em production; boot **falha** em production sem `PAYMENT_GATEWAY_KEY`
- Os 4 exemplos de `api.http` respondendo com status e corpo originais
- 23 checks de invariantes internas (hash, FK, transação/rollback, cascade, config, persistência)
- 8 checks da agregação do relatório, incluindo matrícula com dois pagamentos, curso sem matrícula, pagamento recusado, curso inativo e matrícula órfã
- Casos de borda de payload: `card` numérico, `c_id` zero/string, JSON malformado, campos ausentes
