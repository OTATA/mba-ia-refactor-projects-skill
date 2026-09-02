================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + SQLite
Files:   12 analyzed | 1.158 lines of code
Date:    2026-09-02

## Summary

**CRITICAL: 7 | HIGH: 7 | MEDIUM: 16 | LOW: 12 — Total: 42 findings**

Domínio: Task Manager API — gestão de tarefas com atribuição a usuários,
categorização, busca, estatísticas e relatórios de produtividade.

Arquitetura atual: **pseudo-camadas**. As pastas `models/`, `routes/`,
`services/` e `utils/` existem, mas toda a lógica de negócio vive dentro
das rotas (Fat Controller). `services/` nunca é importado por ninguém e
`utils/helpers.py` é código morto quase integral.

| Camada | Existe? | Realidade |
|---|---|---|
| Presentation (routes) | ✅ | 733 LOC — parsing + validação + regra de negócio + query + serialização |
| Application (services) | ⚠️ | Só `NotificationService`, **nunca importado** |
| Domain (models) | ⚠️ | Anêmico — `validate_status`/`validate_priority`/`is_overdue` nunca chamados |
| Persistence (repository) | ❌ | Queries SQLAlchemy espalhadas nas rotas |
| Config | ❌ | Hardcoded em `app.py`, incluindo `SECRET_KEY` |
| Utils | ⚠️ | Código morto + constantes duplicadas com literais nas rotas |

---

## Findings

### [CRITICAL] Sensitive Data Exposure — hash de senha vazado na resposta HTTP
**File:** `models/user.py:16-25`
**Description:** `User.to_dict()` inclui o campo `'password'` (o hash) no
dicionário serializado. Esse método é usado nas respostas de
`GET /users/<id>` (`routes/user_routes.py:33`), `POST /users`
(`routes/user_routes.py:85`), `PUT /users/<id>` (`routes/user_routes.py:129`)
e `POST /login` (`routes/user_routes.py:209`).
**Impact:** Qualquer cliente da API recebe o hash de senha de qualquer
usuário. Combinado com MD5 sem salt (finding seguinte), isso equivale a
vazar as senhas em texto claro — MD5 de senhas curtas é quebrado em
segundos por rainbow table.
**Recommendation:** O model nunca deve decidir o formato de saída. Criar
serializers/DTOs explícitos por caso de uso, com whitelist de campos.
Remover `password` de qualquer representação pública.

### [CRITICAL] Broken Cryptography — senhas com MD5 sem salt
**File:** `models/user.py:29` e `models/user.py:32`
**Description:** `hashlib.md5(pwd.encode()).hexdigest()`. MD5 é um hash
rápido de propósito geral, sem salt, sem fator de custo e com colisões
conhecidas desde 2004. `check_password` também compara com `==`,
vulnerável a timing attack.
**Impact:** Base de senhas comprometida em minutos caso o banco vaze.
**Recommendation:** Usar um KDF com salt e custo — `werkzeug.security`
(`generate_password_hash` com `scrypt`/`pbkdf2`, já disponível via Flask)
ou `argon2-cffi`. Comparação via `hmac.compare_digest`/API do KDF.

### [CRITICAL] Exposed Credentials — credenciais SMTP hardcoded
**File:** `services/notification_service.py:7-10`
**Description:** Host, porta, usuário (`taskmanager@gmail.com`) e senha
(`senha123`) fixos no código-fonte, versionados no Git.
**Impact:** Quem tem acesso ao repositório (ou ao histórico) tem a conta
de e-mail da aplicação, podendo enviar phishing em nome do produto.
**Recommendation:** Mover para variáveis de ambiente via `python-dotenv`
(já em `requirements.txt`, nunca usado) + objeto de configuração
centralizado. Rotacionar o segredo exposto.

### [CRITICAL] Exposed Credentials — SECRET_KEY hardcoded
**File:** `app.py:13`
**Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'`.
**Impact:** A chave que assina sessões/cookies do Flask é pública e
adivinhável. Permite forjar sessões assinadas.
**Recommendation:** Ler de variável de ambiente; falhar o boot em
produção se ausente.

### [CRITICAL] Missing Authentication & Authorization — API 100% aberta
**File:** `routes/user_routes.py:185-211` (login), e todos os 22 endpoints
**Description:** `POST /login` devolve `'fake-jwt-token-' + str(user.id)`
(`routes/user_routes.py:210`) — um token não assinado, previsível e que
nenhum endpoint valida. Nenhuma rota tem decorator de autenticação.
`User.is_admin()` (`models/user.py:34-38`) existe e nunca é chamado.
**Impact:** Sem autenticar, um anônimo pode: listar todos os usuários e
seus hashes, deletar qualquer usuário e suas tasks
(`routes/user_routes.py:134-151`), deletar qualquer task, e **se
autopromover a admin** via `PUT /users/<id>` com `{"role": "admin"}`
(`routes/user_routes.py:119-122`). Escalação de privilégio trivial.
**Impact adicional:** o campo `active` também é editável por qualquer um
(`routes/user_routes.py:124-125`), permitindo desativar contas alheias.
**Recommendation:** JWT assinado (`PyJWT`) com expiração, decorator
`@require_auth`/`@require_role` em middleware, e regra de que `role`/
`active` só são alteráveis por admin. Fora do escopo desta refatoração
alterar o contrato de login, mas o token deve deixar de ser falso.

### [CRITICAL] Insecure CORS — todas as origens liberadas
**File:** `app.py:15`
**Description:** `CORS(app)` sem parâmetros libera `Access-Control-Allow-Origin: *`
para todos os 22 endpoints, incluindo `/login` e os endpoints de escrita.
**Impact:** Qualquer site pode chamar a API a partir do browser da vítima.
**Recommendation:** Whitelist explícita de origens via configuração.

### [CRITICAL] Vulnerable Dependencies — 10 CVEs em 4 pacotes
**File:** `requirements.txt:1-6`
**Description:** Versões fixadas contêm vulnerabilidades conhecidas
(verificado em osv.dev / GitHub Advisory Database em 2026-09-02):

| Pacote | Versão | CVE | Corrigido em |
|---|---|---|---|
| flask-cors | 4.0.0 | CVE-2024-1681 (log injection) | 4.0.1 |
| flask-cors | 4.0.0 | CVE-2024-6221 (`Access-Control-Allow-Private-Network` = true por default) | 4.0.2 |
| flask-cors | 4.0.0 | CVE-2024-6839 (regex path matching indevido) | 6.0.0 |
| flask-cors | 4.0.0 | CVE-2024-6844 (CORS matching inconsistente) | 6.0.0 |
| flask-cors | 4.0.0 | CVE-2024-6866 (case sensitivity indevida) | 6.0.0 |
| flask | 3.0.0 | CVE-2026-27205 (falta `Vary: Cookie`) | 3.1.3 |
| requests | 2.31.0 | CVE-2024-35195, CVE-2024-47081 (leak de credenciais `.netrc`), CVE-2026-25645 | 2.33.0 |
| marshmallow | 3.20.1 | CVE-2025-68480 (DoS em `Schema.load(many)`) | 3.26.2 / 4.1.2 |
| python-dotenv | 1.0.0 | CVE-2026-28684 (symlink following em `set_key`) | 1.2.2 |

**Impact:** As três CVEs de matching do flask-cors afetam diretamente
esta aplicação, que usa CORS em produção.
**Recommendation:** Atualizar todas as dependências para as versões
corrigidas. `requests` e `marshmallow` sequer são importados — remover.

---

### [HIGH] Fat Controller — rotas com acesso direto ao banco e regra de negócio
**File:** `routes/task_routes.py:1-299`, `routes/user_routes.py:1-211`,
`routes/report_routes.py:1-223` (733 LOC)
**Description:** Cada handler faz, no mesmo corpo: parsing do request,
validação de entrada, regra de negócio, construção de query SQLAlchemy,
gestão de transação (`db.session.commit`/`rollback`) e serialização da
resposta. Exemplos: `create_task` (`routes/task_routes.py:85-154`),
`update_task` (`routes/task_routes.py:156-223`), `summary_report`
(`routes/report_routes.py:12-101`).
**Impact:** Nada é testável sem subir Flask e um banco. Regra de negócio
não é reutilizável fora do HTTP. Qualquer mudança de contrato HTTP
arrisca quebrar regra de domínio e vice-versa.
**Recommendation:** Separar em Controller (HTTP) → Service (regra) →
Repository (persistência), com validators e serializers dedicados.

### [HIGH] Poor Layer Separation — camadas órfãs / código morto
**File:** `services/notification_service.py:1-48`, `utils/helpers.py:57-116`
**Description:** `NotificationService` não é importado em nenhum arquivo
do projeto — a pasta `services/` existe só de fachada.
`utils/helpers.py:57-108` define `process_task_data()`, que centralizaria
toda a validação de task, e nunca é chamado; as rotas reimplementam a
mesma validação à mão. As constantes `utils/helpers.py:110-116`
(`VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, …) nunca são usadas,
enquanto os mesmos valores aparecem como literais em `routes/`.
`format_date` e `calculate_percentage` são importados em
`routes/report_routes.py:7` e nunca chamados.
**Impact:** A estrutura de pastas mente sobre a arquitetura. Duas fontes
de verdade para a mesma regra, garantindo divergência com o tempo.
**Recommendation:** Ou a camada é usada, ou é removida. Consolidar as
regras em um único lugar e fazer as rotas dependerem dele.

### [HIGH] Anemic Domain Model — model tem os métodos e ninguém chama
**File:** `models/task.py:38-60`
**Description:** `Task.validate_status()`, `Task.validate_priority()` e
`Task.is_overdue()` estão implementados e **nunca são invocados**. As
rotas duplicam a mesma lógica inline.
**Impact:** A regra canônica e a regra efetiva podem divergir sem que
nenhum teste perceba.
**Recommendation:** Mover as invariantes para o domínio e consumi-las a
partir de uma única camada.

### [HIGH] Exception Swallowing — 12 blocos `except:` nus
**File:** `routes/task_routes.py:62`, `:137`, `:204`, `:236`;
`routes/user_routes.py:130`, `:149`;
`routes/report_routes.py:186`, `:207`, `:221`;
`utils/helpers.py:46`, `:49`, `:88`
**Description:** `except:` sem classe captura `BaseException`, incluindo
`KeyboardInterrupt` e `SystemExit`. Em `routes/task_routes.py:62-63` todo
o `GET /tasks` está embrulhado num `try/except: return 500 'Erro interno'`,
sem log — um `AttributeError` num campo passa a "erro interno" silencioso.
**Impact:** Bugs indistinguíveis de falhas de infra; debugging impossível;
o processo não responde corretamente a sinais.
**Recommendation:** Capturar exceções específicas, logar com stack trace e
centralizar a tradução exceção→HTTP num error handler.

### [HIGH] Unvalidated Type Coercion — 500 em input malformado
**File:** `routes/task_routes.py:113`, `:182`, `:167`, `:261`, `:264`
**Description:** Vários caminhos assumem o tipo do JSON sem checar:
- `routes/task_routes.py:113` — `if priority < 1 or priority > 5` lança
  `TypeError` se `priority` vier como string (`{"priority": "alta"}`).
- `routes/task_routes.py:182` — idem no update.
- `routes/task_routes.py:167` — `len(data['title'])` lança `TypeError`
  para `{"title": null}` ou `{"title": 5}`.
- `routes/task_routes.py:261` e `:264` — `int(priority)` / `int(user_id)`
  lançam `ValueError` para `?priority=abc`, sem nenhum `try`.
**Impact:** HTTP 500 (erro do servidor) onde deveria ser 400 (erro do
cliente), com stack trace exposto se `debug=True`. `create_task` também
aceita `priority` string que passa a validação e corrompe o dado.
**Recommendation:** Schema de validação declarativo na borda (marshmallow
ou validators próprios) que coage e rejeita antes de tocar no domínio.

### [HIGH] No Migrations — `db.create_all()` em tempo de import
**File:** `app.py:30-31`
**Description:** `with app.app_context(): db.create_all()` roda como
efeito colateral do import de `app.py`. Não há Alembic/Flask-Migrate.
**Impact:** Nenhuma evolução de schema controlada — `create_all()` só cria
tabelas ausentes, jamais altera colunas. Adicionar um campo exige dropar
o banco. Importar `app` num teste ou num script já cria arquivos.
**Recommendation:** Application factory + Flask-Migrate/Alembic; criar
schema por comando explícito, não por import.

### [HIGH] Insecure Defaults — `debug=True` em `0.0.0.0`
**File:** `app.py:33-34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` — o
debugger interativo do Werkzeug exposto em todas as interfaces de rede.
Não há entrypoint WSGI de produção (gunicorn/uwsgi).
**Impact:** O debugger permite execução de código no processo; o PIN é a
única barreira. Stack traces com código-fonte expostos ao cliente.
**Recommendation:** `debug` vindo de configuração (default `False`),
bind em `127.0.0.1` para dev, e gunicorn em produção.

---

### [MEDIUM] N+1 Query — 4 ocorrências
**File:** `routes/task_routes.py:41-57`, `routes/report_routes.py:55-68`,
`routes/report_routes.py:157-164`, `routes/user_routes.py:22`
**Description:**
- `routes/task_routes.py:41-57` — para cada task, um `User.query.get()` e
  um `Category.query.get()`. Com 500 tasks: **1.001 queries** em `GET /tasks`.
- `routes/report_routes.py:55-68` — um `Task.query.filter_by(user_id=…)`
  por usuário dentro do loop.
- `routes/report_routes.py:157-164` — um `COUNT` por categoria.
- `routes/user_routes.py:22` — `len(u.tasks)` dispara lazy-load da coleção
  inteira de tasks para **cada** usuário só para contar.
**Impact:** Latência linear no volume de dados; `GET /tasks` degrada até
timeout. As relações já existem (`models/task.py:20-21`) e não são usadas.
**Recommendation:** Eager loading (`joinedload`/`selectinload`) e
agregação no banco (`func.count` + `GROUP BY`), não em Python.

### [MEDIUM] Query Storm — 14 COUNTs onde bastava 1 GROUP BY
**File:** `routes/report_routes.py:19-28`, `routes/task_routes.py:275-281`
**Description:** `summary_report` dispara 4 counts por status + 5 counts
por prioridade + 3 counts de total = 12 round-trips; `task_stats` dispara
5. Todos são agregações sobre a mesma tabela.
**Impact:** 12 round-trips ao banco por request de relatório.
**Recommendation:** Um `SELECT status, COUNT(*) ... GROUP BY status` e um
`GROUP BY priority`.

### [MEDIUM] Full Table Scan em memória para calcular "overdue"
**File:** `routes/report_routes.py:30-43`, `routes/task_routes.py:281-287`
**Description:** `Task.query.all()` carrega a tabela inteira só para
contar atrasadas num loop Python.
**Impact:** Consumo de memória proporcional à tabela; não escala.
**Recommendation:** Filtro no banco (`due_date < now AND status NOT IN (...)`).

### [MEDIUM] Duplicated Business Rule — lógica de "overdue" repetida 7×
**File:** `models/task.py:50-60` (canônica, nunca usada),
`routes/task_routes.py:30-39`, `:71-80`, `:284-287`,
`routes/user_routes.py:171-180`,
`routes/report_routes.py:34-43`, `:132-135`
**Description:** A mesma condição (`due_date` no passado E status não é
`done`/`cancelled`) reescrita à mão sete vezes, cada uma com aninhamento
de `if/else` diferente.
**Impact:** Corrigir a regra exige achar e editar 7 lugares; a versão
canônica em `Task.is_overdue()` já está órfã.
**Recommendation:** Uma única definição no domínio, consumida por todos.

### [MEDIUM] Duplicated Serialization — `to_dict()` reimplementado à mão
**File:** `routes/task_routes.py:17-28`, `routes/user_routes.py:15-23`,
`routes/user_routes.py:162-169`
**Description:** `routes/task_routes.py:17-28` reconstrói campo a campo
exatamente o que `Task.to_dict()` (`models/task.py:23-36`) já produz.
`routes/user_routes.py:162-169` faz uma terceira variante parcial.
**Impact:** Três formatos de resposta para a mesma entidade, que divergem
a cada mudança de campo.
**Recommendation:** Serializers explícitos e reutilizados.

### [MEDIUM] Duplicated Validation — create vs. update
**File:** `routes/task_routes.py:96-124` vs. `:166-198`;
`routes/user_routes.py:61-72` vs. `:106-122`
**Description:** Limites de título, lista de status válidos, faixa de
prioridade, existência de user/category, regex de e-mail, tamanho mínimo
de senha e lista de roles são validados duas vezes, com mensagens de erro
inconsistentes entre as duas ("Título muito curto" vs. "Título deve ter
entre 3 e 200 caracteres" em `utils/helpers.py:67`).
**Impact:** Divergência garantida. `update_task` já é mais permissivo que
`create_task` (não rejeita título vazio da mesma forma).
**Recommendation:** Um validator por entidade, parametrizado por modo
(criação/atualização parcial).

### [MEDIUM] Long Function / High Cyclomatic Complexity
**File:** `routes/task_routes.py:156-223` (`update_task`, 68 LOC, ~20 branches),
`routes/task_routes.py:85-154` (`create_task`, 70 LOC),
`routes/report_routes.py:12-101` (`summary_report`, 90 LOC, 30+ statements)
**Description:** Funções longas, com múltiplos níveis de aninhamento e
muitos pontos de retorno, misturando níveis de abstração.
**Impact:** Impossível cobrir por teste com confiança; alto risco de
regressão a cada edição.
**Recommendation:** Extrair validação, montagem e persistência; manter
funções curtas e de responsabilidade única.

### [MEDIUM] Missing Pagination — endpoints retornam tabelas inteiras
**File:** `routes/task_routes.py:14`, `:266`; `routes/user_routes.py:12`,
`:35`, `:159`; `routes/report_routes.py:30`, `:53`, `:109`, `:159`
**Description:** Nenhum endpoint de listagem aceita `limit`/`offset`.
`GET /users/<id>` (`routes/user_routes.py:35-38`) embute **todas** as
tasks do usuário na resposta.
**Impact:** Payload e uso de memória ilimitados; DoS trivial por volume.
**Recommendation:** Paginação com limite máximo em todas as listagens.

### [MEDIUM] Wrong Module Boundary — CRUD de Category dentro de reports
**File:** `routes/report_routes.py:157-223`
**Description:** As quatro rotas `/categories` (GET/POST/PUT/DELETE) estão
no blueprint `reports`. Categoria não é relatório.
**Impact:** Localizar o código de categorias é contraintuitivo; o
blueprint acumula responsabilidades não relacionadas.
**Recommendation:** Blueprint/controller próprio para Category.

### [MEDIUM] LIKE com wildcards não escapados e case-sensitive
**File:** `routes/task_routes.py:250-255`
**Description:** `Task.title.like(f'%{query}%')` — os metacaracteres `%` e
`_` vindos do usuário são interpretados como wildcards. Buscar `100%`
retorna tudo. Não é SQL Injection (o ORM faz o bind do parâmetro), mas é
semântica incorreta. `like` também é case-sensitive.
**Impact:** Busca com resultado errado; `q=%` faz full scan.
**Recommendation:** Escapar `%`/`_` com `escape=` e usar `ilike`.

### [MEDIUM] Referential Integrity na aplicação, não no banco
**File:** `routes/user_routes.py:140-142`, `routes/report_routes.py:211-223`
**Description:** `delete_user` deleta as tasks do usuário manualmente em
loop porque as relações (`models/task.py:20-21`) não declaram `cascade`
nem as FKs têm `ON DELETE`. Pior: `delete_category`
(`routes/report_routes.py:211-223`) **não faz nada** com as tasks — deixa
`tasks.category_id` apontando para uma categoria inexistente.
**Impact:** Dados órfãos após deletar categoria; `GET /tasks` retorna
`category_name: null` para tasks que tinham categoria. Deleção de usuário
com muitas tasks emite N DELETEs.
**Recommendation:** Declarar a política de cascade/`SET NULL` no schema e
deixar o banco garanti-la.

### [MEDIUM] Transaction Boundary acidental
**File:** `routes/user_routes.py:140-151`
**Description:** As tasks são marcadas para deleção **fora** do `try`
(`:140-142`) e o `try/except` só envolve o `delete(user)` + `commit`
(`:144-151`). A atomicidade só funciona por acidente (o rollback pega
tudo da sessão), não por desenho.
**Impact:** Estrutura frágil: qualquer `commit` intermediário futuro
quebraria a atomicidade sem aviso.
**Recommendation:** Unidade de trabalho explícita, com o bloco
transacional cobrindo toda a operação.

### [MEDIUM] Weak Password Policy — mínimo de 4 caracteres
**File:** `routes/user_routes.py:64-65`, `:115-116`, `utils/helpers.py:114`
**Description:** `len(password) < 4`. O `seed.py:19,26,33` cria usuários
com as senhas `1234`, `abcd`, `pass`.
**Impact:** Brute force trivial, agravado pelo MD5 sem salt.
**Recommendation:** Mínimo de 8+ caracteres, configurável.

### [MEDIUM] Broken Email Validation
**File:** `routes/user_routes.py:61`, `:106`, `utils/helpers.py:21`
**Description:** `r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'` aceita `a@b`
(sem TLD) e `x@-.-`. O mesmo regex está duplicado em três lugares.
**Impact:** E-mails inválidos persistidos; notificações nunca entregues.
**Recommendation:** Validação única e mais estrita (exigir domínio com
TLD), definida num só lugar.

### [MEDIUM] `print()` como logging — 21 ocorrências
**File:** `routes/task_routes.py:149`, `:153`, `:219`, `:234`;
`routes/user_routes.py:83`, `:89`, `:147`;
`services/notification_service.py:21`, `:24`;
`utils/helpers.py:39-41`; `seed.py:93-96`
**Description:** Diagnóstico via `print` para stdout, sem níveis, sem
timestamp estruturado, sem stack trace. Em
`routes/user_routes.py:89` o erro real é impresso e o cliente recebe uma
mensagem genérica — a informação se perde no stdout do container.
**Impact:** Sem observabilidade em produção; impossível filtrar por
severidade ou correlacionar requests.
**Recommendation:** `logging` configurado, com níveis e handler único.

### [MEDIUM] Notificações em memória e SMTP bloqueante sem timeout
**File:** `services/notification_service.py:6`, `:12-25`, `:31-36`
**Description:** `self.notifications = []` — estado em memória do
processo: perdido em restart e não compartilhado entre workers.
`smtplib.SMTP(host, port)` (`:15`) não define `timeout`, e o envio é
síncrono.
**Impact:** Se o serviço estiver ativo e o SMTP não responder, o worker
fica pendurado indefinidamente. `get_notifications` (`:43-48`) devolve
resultados diferentes conforme o worker que atender.
**Recommendation:** Persistir notificações no banco; envio assíncrono
(fila) e `timeout` explícito no cliente SMTP.

### [MEDIUM] Ausência total de testes
**File:** (projeto inteiro)
**Description:** Nenhum arquivo de teste, nenhum runner configurado,
`pytest` ausente de `requirements.txt`.
**Impact:** Nenhuma rede de segurança para a refatoração — qualquer
mudança é uma aposta.
**Recommendation:** Suíte de testes cobrindo os 22 endpoints antes/junto
da refatoração, garantindo que o contrato HTTP não muda.

---

### [LOW] Unused Imports em 6 arquivos
**File:** `app.py:7` (`os`, `sys`, `json`),
`routes/task_routes.py:7` (`json`, `os`, `sys`, `time` — todos),
`routes/user_routes.py:6` (`hashlib`, `json`),
`routes/report_routes.py:7-8` (`format_date`, `calculate_percentage`, `json`),
`models/task.py:3` (`json`),
`utils/helpers.py:3-7` (`os`, `json`, `sys`, `math`, `hashlib`)
**Impact:** Ruído; sugere dependências que não existem.
**Recommendation:** Remover; adotar linter (ruff/flake8).

### [LOW] Dependências declaradas e nunca usadas
**File:** `requirements.txt:4-6`
**Description:** `marshmallow`, `requests` e `python-dotenv` não são
importados em nenhum arquivo.
**Impact:** Superfície de ataque e tempo de build sem contrapartida —
duas delas com CVE (ver finding CRITICAL de dependências).
**Recommendation:** Remover ou efetivamente usar (`python-dotenv` e
`marshmallow` são justamente o que falta para config e validação).

### [LOW] `type(x) == list` em vez de `isinstance`
**File:** `routes/task_routes.py:141`, `:210`, `utils/helpers.py:103`
**Impact:** Quebra com subclasses de `list`; contraria o idioma da linguagem.
**Recommendation:** `isinstance(x, list)`.

### [LOW] `if cond: return True else: return False`
**File:** `models/user.py:34-38`, `models/task.py:38-43`, `:45-48`, `:50-60`,
`utils/helpers.py:19-23`, `:52-55`
**Description:** Condicionais que apenas reembalam um booleano, com até
três níveis de aninhamento em `models/task.py:50-60`.
**Impact:** Verbosidade que esconde a regra real.
**Recommendation:** Retornar a expressão diretamente.

### [LOW] Magic Numbers e Magic Strings
**File:** status: `routes/task_routes.py:110`, `:177`, `models/task.py:39`,
`utils/helpers.py:75`, `:110`;
roles: `routes/user_routes.py:71`, `:120`, `utils/helpers.py:111`;
faixa 1..5: `routes/task_routes.py:113`, `:182`, `models/task.py:46`,
`utils/helpers.py:84`;
limites 3/200: `routes/task_routes.py:96`, `:99`, `:167`, `:169`,
`utils/helpers.py:64`, `:112-113`;
`'#000000'`: `models/category.py:10`, `routes/report_routes.py:180`,
`utils/helpers.py:116`
**Description:** As mesmas listas e limites repetidos como literais em até
cinco arquivos — e as constantes que os representariam
(`utils/helpers.py:110-116`) existem sem uso.
**Impact:** Mudar um valor exige varredura no projeto inteiro.
**Recommendation:** Enums/constantes num módulo de domínio, importadas.

### [LOW] Poor Naming
**File:** `routes/report_routes.py:24-28` (`p1`…`p5`),
`routes/task_routes.py:16` (`t`), `:51` (`cat`),
`routes/user_routes.py:14` (`u`), `routes/report_routes.py:161` (`c`),
`models/category.py:14` (`d`), `seed.py:78-79` (`td`, `t`),
`utils/helpers.py:57` (`process_task_data` — "process" não diz nada),
`models/task.py:45` (`p`)
**Impact:** Leitura exige rastrear a origem de cada variável.
**Recommendation:** Nomes que digam o quê, não o tipo.

### [LOW] Loops acumuladores manuais
**File:** `routes/report_routes.py:59-61`, `:119-135`;
`routes/task_routes.py:283-287`; `routes/user_routes.py:37-38`;
`services/notification_service.py:44-48`
**Description:** `contador = contador + 1` em loop, e listas construídas
com `append` onde caberia comprehension — ou, melhor, agregação em SQL.
**Impact:** Mais linhas, mais chance de erro, mais lento.
**Recommendation:** Comprehensions/`sum()`; agregação no banco quando
possível.

### [LOW] Datas serializadas com `str()` em vez de ISO 8601
**File:** `models/task.py:32-34`, `models/user.py:24`,
`models/category.py:19`, `app.py:24`, `routes/report_routes.py:41`, `:71`
**Description:** `str(datetime)` produz `2026-09-02 11:28:00.123456` —
espaço em vez de `T` e sem offset de timezone.
**Impact:** Clientes precisam de parser customizado; ambiguidade de fuso.
**Recommendation:** `.isoformat()`.

### [LOW] `updated_at` atribuído manualmente
**File:** `routes/task_routes.py:215`
**Description:** `task.updated_at = datetime.utcnow()` duplica o
`onupdate=datetime.utcnow` já declarado em `models/task.py:16`.
**Impact:** Duas fontes de verdade para o mesmo campo.
**Recommendation:** Confiar no `onupdate` do ORM.

### [LOW] Wrappers triviais e import dentro de função
**File:** `utils/helpers.py:9-12` (`format_date` = `str()`),
`:14-17` (`calculate_percentage`), `:31-34` (`generate_id` com
`import uuid` no corpo da função)
**Description:** Funções que não adicionam valor sobre a biblioteca padrão
e nunca são chamadas. Import local sem motivo (não há ciclo nem custo).
**Impact:** Indireção sem benefício.
**Recommendation:** Remover; imports no topo do módulo.

### [LOW] `SQLALCHEMY_TRACK_MODIFICATIONS` redundante
**File:** `app.py:12`
**Description:** Já é `False` por padrão no Flask-SQLAlchemy 3.x.
**Impact:** Ruído de configuração.
**Recommendation:** Remover.

### [LOW] Falta `.gitignore`, `.env.example` e config de lint
**File:** (raiz do projeto)
**Description:** Sem `.gitignore`, o banco `tasks.db` e `__pycache__/`
entram no repositório. Sem `.env.example`, não há documentação das
variáveis necessárias.
**Impact:** Dados locais versionados; onboarding por tentativa e erro.
**Recommendation:** Adicionar os três arquivos.

---

## Deprecated API / Dependency Report

Verificação feita contra documentação oficial e reproduzida localmente
(Python 3.13.7, SQLAlchemy 2.0.43 instalados nesta máquina).

### 1. `datetime.datetime.utcnow()` — 18 ocorrências
| | |
|---|---|
| **API depreciada** | `datetime.datetime.utcnow()` |
| **Versão do projeto** | Python 3.13.7 |
| **Depreciada desde** | Python 3.12 |
| **Substituto** | `datetime.datetime.now(datetime.UTC)` |
| **Remoção** | "scheduled for removal in a future version" (sem versão fixada) |
| **Fonte** | https://docs.python.org/3/library/datetime.html — *"Deprecated since version 3.12: … the recommended way to create an object representing the current time in UTC is by calling `datetime.now(timezone.utc)`"* |

Aviso reproduzido localmente:
> `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).`

**Ocorrências:** `models/task.py:15`, `:16`, `:52`;
`models/user.py:14`; `models/category.py:11`;
`routes/task_routes.py:31`, `:72`, `:215`, `:285`;
`routes/user_routes.py:172`;
`routes/report_routes.py:35`, `:42`, `:45`, `:71`, `:133`;
`services/notification_service.py:35`; `utils/helpers.py:38`;
`seed.py:66-75` (múltiplas na lista de dados)

**Observação de correção:** o projeto grava datas *naive* no banco
(`db.DateTime` sem `timezone=True`). A troca por `now(UTC)` produz datas
*aware*, e comparar aware com naive lança `TypeError`. A migração precisa
ser consistente: ou coluna `DateTime(timezone=True)` em todo o schema, ou
`datetime.now(UTC).replace(tzinfo=None)` para manter o comportamento
atual. Sem isso, a "correção" quebra `is_overdue` e os relatórios.

### 2. `Query.get()` — 16 ocorrências
| | |
|---|---|
| **API depreciada** | `Model.query.get(pk)` / `Query.get()` |
| **Versão do projeto** | SQLAlchemy 2.0.43 (via Flask-SQLAlchemy 3.1.1) |
| **Depreciada desde** | SQLAlchemy 2.0 (legacy desde 1.4) |
| **Substituto** | `db.session.get(Model, pk)` |
| **Remoção** | Não documentada; mantida como legacy |
| **Fonte** | https://docs.sqlalchemy.org/en/20/changelog/migration_20.html — *"The `Query.get()` method remains for legacy purposes, but the primary interface is now the `Session.get()` method"* |

Aviso reproduzido localmente:
> `LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get() (deprecated since: 2.0)`

**Ocorrências:** `routes/task_routes.py` (9), `routes/user_routes.py` (4),
`routes/report_routes.py` (3).

### 3. Interface `Model.query` (legacy Query API) — 57 ocorrências
| | |
|---|---|
| **API depreciada** | `Model.query` / `Session.query()` |
| **Versão do projeto** | Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.0.43 |
| **Status** | Legacy (não emite warning, mas explicitamente desaconselhada) |
| **Substituto** | `db.session.execute(db.select(Model)…)` |
| **Remoção** | Não documentada; "long term legacy objects" |
| **Fonte** | https://flask-sqlalchemy.readthedocs.io/en/stable/queries/ — *"That query interface is considered legacy in SQLAlchemy. Prefer using the `session.execute(select(...))` instead."* / https://docs.sqlalchemy.org/en/20/changelog/migration_20.html — *"The `Query` object … become long term legacy objects, replaced by the direct usage of the `select()` construct"* |

**Ocorrências:** `routes/report_routes.py` (23), `routes/task_routes.py` (17),
`routes/user_routes.py` (11), `seed.py` (6).

### 4. Dependências desatualizadas com CVE
Ver o finding **[CRITICAL] Vulnerable Dependencies**. Versões atuais no
PyPI em 2026-09-02: flask 3.1.3, flask-sqlalchemy 3.1.1 (já atual),
flask-cors 6.0.5, marshmallow 4.3.1, requests 2.34.2, python-dotenv 1.2.3.

### 5. Verificado e **não** depreciado
- `hashlib.md5` — **não** está depreciada em Python 3.13; é insegura para
  senhas, mas por escolha de algoritmo, não por depreciação. Reportada
  como finding de segurança, não de API depreciada.
- `db.Column` / estilo declarativo clássico — suportado no
  Flask-SQLAlchemy 3.1; `Mapped`/`mapped_column` é recomendado para
  código novo, mas o estilo antigo **não** está depreciado.
- `flask_sqlalchemy.SQLAlchemy` e `flask_cors.CORS` — APIs atuais.
- `datetime.strptime` — atual.

================================
Total: 42 findings + 3 APIs depreciadas em uso (91 chamadas)
================================
