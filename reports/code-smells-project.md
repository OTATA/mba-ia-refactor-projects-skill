# ARCHITECTURE AUDIT REPORT

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Persistence:   SQLite 3 (stdlib sqlite3, raw SQL, no ORM) — loja.db
Domain:        E-commerce API (produtos, usuários, pedidos, relatório de vendas)
Architecture:  Monolito plano — 4 arquivos no diretório raiz, sem camadas.
               app.py mistura composition root + rotas + handlers com SQL.
               "models.py" é na verdade data-access + regra de negócio + mapeamento.
               "controllers.py" concentra validação, orquestração, notificação e HTTP.
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 (6 produtos, 4 usuários/auth, 4 pedidos, 1 relatório,
               1 health, 1 index, 2 admin sem autenticação)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1 + SQLite (raw SQL)
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-02
================================
```

## Summary

| Severity | Count |
| --- | --- |
| CRITICAL | 8 |
| HIGH | 7 |
| MEDIUM | 9 |
| LOW | 7 |
| **Total** | **31** |

---

## Findings

### [CRITICAL] Arbitrary SQL Execution Endpoint (unauthenticated)

**File:** `app.py:59-78`
**Description:** `POST /admin/query` lê a string `sql` do corpo da requisição e a repassa
direto para `cursor.execute()`. Não há autenticação, autorização, nem allow-list.
**Impact:** Qualquer chamador anônimo lê o banco inteiro (incluindo senhas em texto puro),
altera preços e estoque, ou executa `DROP TABLE`. É o pior tipo de SQL injection: injeção
por design.
**Recommendation:** Remover o endpoint. Se um console administrativo for necessário, ele
pertence a uma ferramenta operacional fora da API pública.

---

### [CRITICAL] Unauthenticated Destructive Endpoint

**File:** `app.py:47-57`
**Description:** `POST /admin/reset-db` apaga `itens_pedido`, `pedidos`, `produtos` e
`usuarios` sem qualquer verificação de identidade ou permissão.
**Impact:** Perda total de dados acionável por qualquer pessoa que conheça a URL.
**Recommendation:** Remover da API. Bootstrap/seed de banco é responsabilidade de script
de infraestrutura, não de rota HTTP.

---

### [CRITICAL] SQL Injection por concatenação de strings (todo o data-access)

**File:** `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`,
`models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140`,
`models.py:148-151`, `models.py:155-166`, `models.py:174`, `models.py:188`,
`models.py:192`, `models.py:220`, `models.py:224`, `models.py:279-281`,
`models.py:289-299`
**Description:** Nenhuma query usa parâmetros vinculados. Todas montam SQL com `+` e
`str()`. Os vetores diretamente exploráveis por entrada do usuário são:
- `login_usuario` (`models.py:109-111`): `email`/`senha` concatenados no `WHERE` →
  bypass de autenticação com `' OR '1'='1`.
- `buscar_produtos` (`models.py:289-299`): `termo` e `categoria` vêm de query string sem
  escape, dentro de `LIKE '%...%'`.
- `criar_produto` / `criar_usuario` / `atualizar_produto` (`models.py:47-50`, `126-129`,
  `57-61`): `nome`, `descricao`, `email` interpolados em `INSERT`/`UPDATE`.
**Impact:** Bypass de login, exfiltração da tabela `usuarios`, escrita arbitrária.
Também quebra funcionalmente com qualquer dado legítimo contendo apóstrofo
(ex.: `Monitor 27''`, "D'Angelo").
**Recommendation:** Usar placeholders `?` do `sqlite3` em 100% das queries, com os valores
passados na tupla de parâmetros. Nunca concatenar entrada externa em SQL.

---

### [CRITICAL] Hardcoded Secret Key

**File:** `app.py:7`
**Description:** `SECRET_KEY` fixada no código como `"minha-chave-super-secreta-123"` e
commitada no repositório.
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar sessões/cookies
assinados. A chave não pode ser rotacionada sem novo deploy de código.
**Recommendation:** Ler de variável de ambiente em um módulo de configuração; falhar o
boot se ausente em produção.

---

### [CRITICAL] Sensitive Configuration Exposed via API

**File:** `controllers.py:285-289`
**Description:** `GET /health` devolve no corpo da resposta `db_path`, `debug: true`,
`ambiente: "producao"` e `secret_key: "minha-chave-super-secreta-123"`.
**Impact:** Vaza o segredo da aplicação para qualquer cliente não autenticado, além de
confirmar que o modo debug está ativo em produção.
**Recommendation:** Health check deve devolver apenas liveness/readiness. Nunca serializar
configuração ou segredos.

---

### [CRITICAL] Passwords Stored and Compared in Plaintext

**File:** `database.py:31`, `database.py:75-83`, `models.py:110`, `models.py:126-129`
**Description:** A coluna `usuarios.senha` guarda a senha literal. O cadastro insere o
valor cru (`models.py:126-129`) e o login compara com igualdade de string dentro do SQL
(`models.py:110`). O seed já grava `admin123`, `123456`, `senha123`.
**Impact:** Vazamento do banco expõe todas as credenciais em claro; usuários que reciclam
senhas ficam comprometidos em outros serviços.
**Recommendation:** Derivar hash com algoritmo adequado (`werkzeug.security`
`generate_password_hash`/`check_password_hash`, ou bcrypt/argon2). Verificar o hash na
camada de aplicação, buscando o usuário por email e comparando em memória.

---

### [CRITICAL] Password Field Returned by User Endpoints

**File:** `models.py:83-84`, `models.py:99-100`
**Description:** O mapeamento de `usuarios` inclui `"senha": row["senha"]`, e esse dict é
serializado direto por `GET /usuarios` (`controllers.py:128-134`) e
`GET /usuarios/<id>` (`controllers.py:136-144`).
**Impact:** `curl /usuarios` devolve a lista completa de emails e senhas. Não há
autenticação na rota.
**Recommendation:** Construir a resposta a partir de um serializer explícito que omite
`senha`. Nunca serializar a entidade de persistência diretamente.

---

### [CRITICAL] Debug Mode Enabled in Production

**File:** `app.py:8`, `app.py:88`
**Description:** `app.config["DEBUG"] = True` e `app.run(debug=True)` estão fixos no
código, com o servidor escutando em `0.0.0.0`.
**Impact:** O debugger interativo do Werkzeug expõe um console Python em qualquer traceback
— execução remota de código. Tracebacks completos também revelam o código-fonte.
**Recommendation:** `DEBUG` deve vir de configuração de ambiente com default `False`.
Servir com WSGI de produção; nunca `app.run` com debug em host público.

---

### [HIGH] God Module: models.py

**File:** `models.py:1-314`
**Description:** Um módulo de 314 linhas acumula, para 4 domínios distintos: montagem de
SQL, acesso a conexão, mapeamento linha→dict, regra de negócio de pedido (validação de
estoque, cálculo de total, baixa de estoque) e regra de negócio de faturamento (faixas de
desconto em `models.py:256-262`).
**Impact:** Nada é testável em isolamento — qualquer teste precisa de banco real.
Alterar o cálculo de desconto e alterar a listagem de produtos tocam o mesmo arquivo.
**Recommendation:** Separar por domínio e por responsabilidade: repositórios (SQL),
models/entidades (invariantes de domínio), services (orquestração).

---

### [HIGH] Controller with Direct Database Access

**File:** `controllers.py:264-292`, `app.py:47-57`, `app.py:59-78`
**Description:** `health_check` abre conexão, cria cursor e executa 4 queries SQL
diretamente na camada HTTP (`controllers.py:266-274`). As rotas `/admin/reset-db` e
`/admin/query` executam SQL dentro do próprio `app.py`.
**Impact:** Persistência espalhada por três camadas; impossível trocar o mecanismo de
acesso a dados ou mockar para teste.
**Recommendation:** Todo SQL atrás de repositório. Controller apenas delega.

---

### [HIGH] Missing Layer Separation / Business Logic in Controllers

**File:** `controllers.py:43-54`, `controllers.py:87-90`, `controllers.py:208-210`,
**File:** `controllers.py:242`, `controllers.py:247-250`
**Description:** Regras que valem independentemente do transporte moram no controller:
faixas válidas de preço/estoque/nome (`43-50`), lista de categorias válidas (`52-54`),
lista de status válidos (`242`), e efeitos colaterais de negócio — disparo de
email/SMS/push (`208-210`) e notificações por transição de status (`247-250`).
**Impact:** As mesmas regras teriam de ser reimplementadas em qualquer outro ponto de
entrada (worker, CLI, mensageria). Não há camada onde a regra viva uma única vez.
**Recommendation:** Mover invariantes de domínio para models/services; controller faz
apenas validação de forma da requisição e tradução de erro → status HTTP.

---

### [HIGH] Duplicated Domain Validation Between Create and Update

**File:** `controllers.py:28-54` vs `controllers.py:72-90`
**Description:** `criar_produto` e `atualizar_produto` repetem, quase literalmente, o
mesmo bloco de validação — porém divergentes: o update **não** valida tamanho de nome
nem categoria válida.
**Impact:** A divergência já é um bug: é possível gravar via `PUT` um produto com nome de
1 caractere ou categoria inexistente, estados que o `POST` rejeita.
**Recommendation:** Extrair um validador único de produto, usado pelos dois fluxos.

---

### [HIGH] No Authentication or Authorization Layer

**File:** `app.py:11-30`, `controllers.py:167-186`
**Description:** Nenhuma rota exige identidade. `login` (`controllers.py:176-180`) valida
credenciais mas não emite token nem sessão — o resultado é puramente informativo.
Consequentemente, listar usuários, alterar status de pedido, deletar produto e ler o
relatório de vendas são operações anônimas.
**Impact:** Não existe controle de acesso. `SECRET_KEY` é configurada mas nunca usada.
**Recommendation:** Introduzir autenticação (sessão assinada ou token) e um decorator de
autorização aplicado às rotas de escrita e às rotas administrativas.

---

### [HIGH] Non-Atomic Order Creation with Stock Race Condition

**File:** `models.py:133-169`
**Description:** `criar_pedido` valida estoque em um laço (`139-146`), depois insere o
pedido, os itens e decrementa estoque em um segundo laço (`154-166`), com um único
`db.commit()` no fim (`168`). Não há `BEGIN` explícito, `rollback()`, nem tratamento de
exceção. Dois pedidos concorrentes para o mesmo produto podem ambos passar a validação.
**Impact:** Estoque negativo; se uma exceção ocorrer no meio do segundo laço, a transação
implícita fica aberta na conexão global compartilhada, bloqueando as próximas requisições.
**Recommendation:** Envolver a operação inteira em transação com `rollback` em falha,
e fazer a baixa de estoque com condição (`UPDATE ... WHERE estoque >= ?`) verificando
`rowcount`.

---

### [HIGH] Single Global Database Connection Shared Across Threads

**File:** `database.py:4-11`
**Description:** Uma única `sqlite3.Connection` global é criada com
`check_same_thread=False` e reutilizada por todas as requisições. O servidor Flask atende
em múltiplas threads.
**Impact:** Cursores e estado transacional compartilhados entre requisições concorrentes →
resultados intercalados, `lastrowid` incorreto e commits de trabalho parcial de outra
requisição. `check_same_thread=False` silencia a proteção do driver sem resolver a causa.
**Recommendation:** Conexão por requisição (padrão `flask.g` + `teardown_appcontext`) ou
pool. Manter a criação de schema fora do caminho de obtenção de conexão.

---

### [MEDIUM] N+1 Queries in Order Listing

**File:** `models.py:171-201`, `models.py:203-233`
**Description:** `get_pedidos_usuario` e `get_todos_pedidos` executam 1 query de pedidos,
depois 1 query de itens por pedido (`188`, `220`), e ainda 1 query de nome de produto por
item (`192`, `224`).
**Impact:** `GET /pedidos` com 100 pedidos de 5 itens dispara 601 queries. Custo cresce
multiplicativamente.
**Recommendation:** Uma query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos`,
agrupando o resultado em memória.

---

### [MEDIUM] Redundant Query Inside Order Creation

**File:** `models.py:139-141` e `models.py:154-156`
**Description:** Cada produto do pedido é buscado duas vezes: o registro completo no laço
de validação e novamente só o preço no laço de inserção.
**Impact:** Dobra as queries por item e abre janela para o preço mudar entre as duas
leituras — o total cobrado pode divergir do `preco_unitario` gravado.
**Recommendation:** Carregar os produtos uma vez, em lote (`WHERE id IN (...)`), e reusar
os valores já lidos.

---

### [MEDIUM] Duplicated Data-Access and Mapping Code

**File:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313` (produto);
`models.py:79-86`, `models.py:95-102` (usuário); `models.py:171-201` vs `models.py:203-233`
(pedido)
**Description:** O mapeamento linha→dict de produto aparece 3 vezes idêntico, o de usuário
2 vezes, e as duas listagens de pedido diferem apenas pela cláusula `WHERE`.
**Impact:** Adicionar um campo exige editar de 2 a 3 lugares; a omissão em um deles produz
contratos de API inconsistentes entre endpoints.
**Recommendation:** Um único mapeador/serializer por entidade; unificar as listagens de
pedido com filtro opcional.

---

### [MEDIUM] Internal Error Details Leaked to Clients

**File:** `controllers.py:12`, `22`, `62`, `96`, `109`, `126`, `134`, `144`, `165`, `186`,
`220`, `227`, `235`, `255`, `262`, `292`; `app.py:78`
**Description:** Todos os 17 handlers repetem `except Exception as e:` devolvendo
`jsonify({"erro": str(e)})` com HTTP 500.
**Impact:** Mensagens do SQLite (nomes de tabela, colunas, fragmentos de SQL) chegam ao
cliente, ajudando a mapear o schema. Também não há distinção entre erro esperado
(não encontrado, validação) e falha inesperada.
**Recommendation:** Error handler centralizado: exceções de domínio mapeadas para status
HTTP com mensagem segura; falhas inesperadas logadas internamente e respondidas com
mensagem genérica.

---

### [MEDIUM] Status Update Applied to Nonexistent Orders

**File:** `models.py:275-283`, `controllers.py:237-252`
**Description:** `atualizar_status_pedido` executa o `UPDATE` e retorna `True`
incondicionalmente, sem checar `cursor.rowcount`.
**Impact:** `PUT /pedidos/9999/status` responde `200 {"sucesso": true}` para um pedido que
não existe, e a notificação de "aprovado"/"cancelado" é disparada
(`controllers.py:247-250`).
**Recommendation:** Verificar existência (ou `rowcount`) e responder 404 quando não houver
linha afetada.

---

### [MEDIUM] Unvalidated Input Types Cause 500 Instead of 400

**File:** `controllers.py:43-46`, `controllers.py:87-90`, `controllers.py:118-121`,
`controllers.py:239-240`
**Description:** `preco` e `estoque` são comparados com `0` sem checagem de tipo — um
payload `{"preco": "abc"}` lança `TypeError` e cai no `except` genérico como 500
(`controllers.py:43`). `float(preco_min)` sem tratamento em `118-121` tem o mesmo efeito.
Em `atualizar_status_pedido` (`239-240`) o retorno de `request.get_json()` é usado sem
verificação de `None`.
**Impact:** Erro de cliente reportado como erro de servidor; ruído em métricas e
alertas, e diagnóstico incorreto.
**Recommendation:** Validação de tipo/coerção na borda, devolvendo 400 com mensagem
descritiva.

---

### [MEDIUM] Validation Ordered After Database Read

**File:** `controllers.py:66-79`
**Description:** `atualizar_produto` consulta o produto no banco (`68`) **antes** de
validar o corpo da requisição (`72-79`).
**Impact:** Requisições malformadas custam uma ida ao banco desnecessária; a ordem também
torna o fluxo mais difícil de seguir.
**Recommendation:** Validar a requisição primeiro, acessar persistência depois.

---

### [MEDIUM] Schema Creation and Seed Data Inside Connection Getter

**File:** `database.py:7-86`
**Description:** `get_db()` acumula três responsabilidades: obter conexão, criar as 4
tabelas (`14-53`) e inserir dados de exemplo, incluindo usuários com senha fixa
(`56-84`).
**Impact:** Não há controle de versão de schema (migrations); o seed com credenciais
conhecidas roda em qualquer ambiente, inclusive produção.
**Recommendation:** Separar conexão de bootstrap de schema; mover seed para script
explícito, restrito a desenvolvimento.

---

### [MEDIUM] `print()` Used as Logging, Including PII

**File:** `controllers.py:8`, `11`, `57`, `61`, `106`, `161`, `179`, `182`, `208-210`,
`219`, `248`, `250`; `app.py:56`, `83-86`
**Description:** Diagnóstico escrito com `print()` para stdout, sem nível, timestamp ou
contexto de requisição. `controllers.py:161`, `179` e `182` registram o email do usuário —
inclusive em tentativas de login falhas.
**Impact:** Sem observabilidade utilizável; PII em logs sem retenção controlada. Os
`print` de `208-210` também simulam integrações que não existem, mascarando a ausência do
comportamento.
**Recommendation:** Usar o `logging` da stdlib com níveis, sem registrar identificadores
pessoais nem credenciais.

---

### [LOW] Magic Numbers in Business Rules

**File:** `models.py:256-262`, `controllers.py:47-50`
**Description:** As faixas de desconto usam literais sem nome — `10000`/`0.1`,
`5000`/`0.05`, `1000`/`0.02`. Os limites de nome de produto usam `2` e `200`.
**Impact:** A intenção da regra não é legível; alterar uma faixa exige localizar o número
correto entre condicionais.
**Recommendation:** Constantes nomeadas junto ao domínio a que pertencem
(preservando exatamente os valores atuais).

---

### [LOW] Duplicated Domain Vocabulary as Inline Literals

**File:** `controllers.py:52`, `controllers.py:242`
**Description:** A lista de categorias válidas e a de status válidos estão escritas como
literais dentro dos handlers, e a de categorias tem `"geral"` também como default em
`controllers.py:41` e `85`.
**Impact:** Adicionar uma categoria ou status exige editar múltiplos pontos, com risco de
divergência silenciosa entre create e update.
**Recommendation:** Declarar o vocabulário uma única vez no domínio.

---

### [LOW] Shadowing the Builtin `id`

**File:** `controllers.py:14`, `56`, `64`, `98`, `136`, `160`; `models.py:24`, `54`, `65`,
`89`
**Description:** O parâmetro/variável `id` sombreia o builtin em 10 pontos, e em
`controllers.py:56` e `160` é reatribuído para o retorno da criação.
**Impact:** Reduz legibilidade e mascara o builtin no escopo da função.
**Recommendation:** Nomes explícitos: `produto_id`, `usuario_id`.

---

### [LOW] Excessive Sequential Conditionals

**File:** `controllers.py:28-54`, `controllers.py:72-90`
**Description:** `criar_produto` tem 10 `if` sequenciais de validação (27 linhas) antes de
qualquer trabalho útil; `atualizar_produto` repete 8.
**Impact:** A responsabilidade real da função fica soterrada pela validação.
**Recommendation:** Extrair para um validador coeso, mantendo as mesmas regras e mensagens.

---

### [LOW] String Concatenation Instead of Formatting

**File:** `controllers.py:8`, `11`, `54`, `57`, `61`, `106`, `161`, `179`, `182`,
`208-210`, `219`, `248`, `250`; `models.py` (todas as queries)
**Description:** Mensagens montadas com `+` e `str()` em vez de f-strings.
**Impact:** Verboso e propenso a erro; em `models.py` é o mesmo hábito que produz o SQL
injection.
**Recommendation:** f-strings para texto; parâmetros vinculados para SQL.

---

### [LOW] Inconsistent Response Envelope

**File:** `controllers.py:20` vs `70`; `124` vs `132`; `162` vs `180`
**Description:** Algumas respostas de erro incluem `"sucesso": False` (`20`, `183`, `206`)
e outras não (`70`, `103`, `142`). Apenas `buscar_produtos` retorna `total` (`124`).
**Impact:** Clientes não podem confiar em um formato único de resposta.
**Recommendation:** Padronizar o envelope em um único ponto de construção de resposta,
mantendo as chaves já existentes no contrato.

---

### [LOW] Unused Imports and Dead Schema Column

**File:** `models.py:2`, `database.py:2`, `database.py:22`
**Description:** `import sqlite3` em `models.py` e `import os` em `database.py` não são
usados. A coluna `produtos.ativo` é criada, mapeada em todas as respostas, e nunca
escrita nem usada como filtro.
**Impact:** Ruído; a coluna sugere um soft-delete que não existe — `deletar_produto`
(`models.py:65-70`) apaga a linha fisicamente.
**Recommendation:** Remover os imports. Manter `ativo` no schema e nas respostas (contrato
atual), sem introduzir comportamento novo.

---

```
================================
Total: 31 findings
================================
```

---

## Deprecated API / Dependency Audit

Verificado contra fontes primárias: changelog oficial do Flask, releases oficiais do
flask-cors no GitHub, metadados do PyPI e a documentação do `sqlite3` da CPython.

### Resultado do código-fonte

Nenhuma API depreciada do Flask ou da stdlib está em uso. As APIs utilizadas —
`Flask`, `jsonify`, `request.get_json`, `request.args`, `add_url_rule`, `route`,
`app.run`, `flask_cors.CORS` — são todas suportadas no Flask 3.1.x.

Duas verificações específicas, ambas negativas:

| Verificação | Situação no projeto | Fonte |
| --- | --- | --- |
| `sqlite3.connect()` com parâmetros posicionais (deprecated em 3.13, remoção em 3.15) | Não afetado — `database.py:10` já usa `check_same_thread=` como keyword | docs.python.org/3/library/sqlite3.html |
| Adaptadores/conversores default de `datetime` no `sqlite3` (deprecated em 3.12) | Não afetado — `detect_types` não é usado; colunas `TIMESTAMP` retornam string | docs.python.org/3/library/sqlite3.html |

### Dependências desatualizadas com correções de segurança

| Dependência | Versão do projeto | Versão atual | Problema | Fonte |
| --- | --- | --- | --- | --- |
| `flask-cors` | 5.0.1 | 6.0.5 (2026-06-08) | Três CVEs corrigidas somente na 6.0.0: **CVE-2024-6839** (ordenação de especificidade de regex de path), **CVE-2024-6844** (`unquote_plus` → `unquote` na decodificação de path), **CVE-2024-6866** (matching de path sensível a caso). Todas afetam versões < 6.0.0. | github.com/corydolphin/flask-cors/releases; pypi.org/pypi/flask-cors/json |
| `flask` | 3.1.1 | 3.1.3 (2026-02-18) | **GHSA-68rp-wp8r-4726**, corrigida na 3.1.3: a sessão não era marcada como acessada em operações que leem apenas as chaves (`in`, `len`). Sem depreciações entre 3.1.1 e 3.1.3. | flask.palletsprojects.com/en/stable/changes/ |

**Nota sobre o upgrade do flask-cors:** a 6.0.0 alterou a ordenação de especificidade de
paths — que é justamente a correção da CVE-2024-6839 — e é a única mudança
incompatível relevante. Este projeto usa `CORS(app)` sem configuração por path
(`app.py:9`), portanto não é afetado pela mudança de comportamento.

### Configuração de CORS irrestrita (não depreciada, mas relacionada)

**File:** `app.py:9`
`CORS(app)` sem argumentos libera `Access-Control-Allow-Origin: *` para todas as rotas,
incluindo as administrativas e as que expõem senhas. Combinado com a ausência de
autenticação, qualquer página web pode consumir a API a partir do navegador da vítima.
**Recommendation:** Restringir `origins` a uma lista explícita vinda de configuração.
