# task-manager-api

API de Task Manager em Python/Flask, refatorada para uma arquitetura em
camadas. O projeto de origem já tinha as pastas `models/`, `routes/`,
`services/` e `utils/`, mas a regra de negócio vivia dentro das rotas e duas
dessas camadas eram código morto.

A auditoria que motivou a refatoração está em
[`../reports/task-manager-api.md`](../reports/task-manager-api.md): 42
achados e 3 APIs depreciadas em uso.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # ajuste SECRET_KEY e CORS_ORIGINS
python seed.py                # popula o banco (rode antes do primeiro boot)
python app.py
```

A aplicação sobe em `http://localhost:5000`.

> **Rode `python seed.py` novamente se estiver vindo da versão anterior.** As
> senhas passaram a ser gravadas com scrypt em vez de MD5, e os hashes antigos
> não são conversíveis — o login com o banco antigo falha.

Em produção, use o servidor WSGI e nunca o `app.run()`:

```bash
APP_ENV=production SECRET_KEY=... gunicorn "app:app" --bind 0.0.0.0:5000
```

Com `APP_ENV=production`, a ausência de `SECRET_KEY` (ou uma chave com menos
de 32 caracteres) interrompe o boot em vez de silenciosamente usar um
segredo fraco.

## Testes

```bash
pytest
```

122 testes cobrindo os 22 endpoints: formato de cada resposta, mensagens de
erro, status codes, política de autorização e as garantias de segurança.
`pytest.ini` trata `DeprecationWarning` e `LegacyAPIWarning` como erro, o que
impede a reintrodução de `datetime.utcnow()` e `Query.get()`.

## Estrutura

```
app.py                          entry point (preserva `python app.py`)
seed.py                         popula o banco com os dados de exemplo
src/
├── app.py                      composition root — create_app()
├── container.py                composição das dependências com configuração
├── exceptions.py               erros de domínio (não conhecem HTTP)
├── extensions.py               instância do SQLAlchemy
├── config/settings.py          configuração lida do ambiente
├── models/                     entidades e invariantes de domínio
│   ├── enums.py                status, roles e limites do domínio
│   ├── task.py  user.py  category.py
├── repositories/               único lugar que constrói queries
│   ├── task_repository.py  user_repository.py  category_repository.py
│   └── unit_of_work.py         fronteira transacional
├── services/                   regras de negócio e orquestração
│   ├── task_service.py  user_service.py  category_service.py
│   ├── auth_service.py  report_service.py  notification_service.py
├── validators/                 validação de forma da requisição
│   ├── task_validator.py  user_validator.py  category_validator.py
├── controllers/                fronteira HTTP — thin
│   ├── requests.py             leitura de entrada compartilhada
│   ├── task_controller.py  user_controller.py  category_controller.py
│   ├── auth_controller.py  report_controller.py  system_controller.py
├── views/                      camada de apresentação
│   ├── routes.py               roteamento + política de acesso
│   ├── serializers.py          entidade → payload público
│   └── responses.py            envelope das respostas
├── middlewares/
│   ├── auth.py                 require_auth / require_role
│   └── error_handler.py        tratamento centralizado de erros
├── security/
│   ├── passwords.py            hash scrypt com salt
│   └── tokens.py               JWT HS256 com expiração
└── infrastructure/
    ├── clock.py                fonte única do "agora" (UTC)
    └── database.py             criação de schema + PRAGMA de FK
```

Direção das dependências:

```
Controller → Validator → Service → Repository → Model
     ↓                       ↓
   View                Unit of Work
```

Nenhum controller constrói query, nenhum service conhece `request`/`jsonify`,
e nenhum model importa Flask.

## Autenticação

`POST /login` devolve um JWT HS256 assinado com a `SECRET_KEY` e com
expiração (`JWT_EXPIRATION_MINUTES`, default 60). Envie-o em todas as rotas
protegidas:

```
Authorization: Bearer <token>
```

| Rota                    | Acesso                       |
|-------------------------|------------------------------|
| `GET /`, `GET /health`  | público                      |
| `POST /login`           | público                      |
| `POST /users`           | público (registro)           |
| `DELETE /users/<id>`    | admin                        |
| `PUT /users/<id>`       | o próprio usuário ou admin   |
| todas as demais         | qualquer usuário autenticado |

Duas regras extras dependem do corpo da requisição e são aplicadas no
controller de usuários:

- `role` e `active` em `PUT /users/<id>` só podem ser alterados por um admin.
- `POST /users` só aceita `role` diferente de `user` se quem chamou for um
  admin autenticado.

Juntas, elas fecham a escalação de privilégio da versão anterior, em que
qualquer anônimo virava admin com um `PUT /users/<id>`.

## O que mudou no contrato da API

As 22 rotas, os payloads de resposta, as mensagens de erro e os status codes
são os mesmos de antes. As exceções:

| Mudança | Motivo |
|---|---|
| Todas as rotas (exceto as 4 públicas) exigem `Authorization: Bearer` | A API não tinha autenticação nenhuma |
| O campo `password` saiu de todas as respostas | Vazava o hash de senha em 4 endpoints |
| `token` é um JWT assinado, não `fake-jwt-token-<id>` | O token anterior era previsível e ninguém o validava |
| `PUT /users/<id>` com `role`/`active` exige admin | Escalação de privilégio |
| Erros de tipo devolvem 400 em vez de 500 | `{"priority": "alta"}` e `?priority=abc` derrubavam o handler |
| `DELETE /categories/<id>` zera `category_id` nas tasks | Antes deixava FK apontando para linha inexistente |
| Busca é case-insensitive e trata `%`/`_` como literais | `?q=%` retornava a tabela inteira |
| `limit`/`offset` opcionais nas listagens | Paginação; sem os parâmetros o comportamento é o de antes |

## O que ficou de fora, e por quê

Achados da auditoria deliberadamente não corrigidos, para não alterar regra
de negócio nem quebrar contrato:

- **Senha mínima de 4 caracteres** (`MIN_PASSWORD_LENGTH`) — é fraca, mas é
  uma regra de negócio; agora está numa constante em `models/enums.py`.
- **Regex de e-mail que aceita `a@b`** — endereços sem TLD passam. Corrigir
  muda o conjunto de e-mails aceitos; o regex foi centralizado sem alteração
  em `validators/user_validator.py`.
- **Datas serializadas como `str()`** e não ISO 8601 — `2026-09-02 11:28:00`
  em vez de `2026-09-02T11:28:00`. Migrar quebra os parsers dos clientes.
- **Listagens sem limite por padrão** — `limit`/`offset` existem, mas impor
  um teto truncaria respostas já em uso.
- **`NotificationService` continua sem ser chamado por nenhum endpoint**,
  como antes. Ele foi mantido e corrigido (credenciais na configuração,
  `timeout` no SMTP, `logging` no lugar de `print`), mas ligá-lo ao fluxo de
  atribuição de task passaria a enviar e-mail onde antes não enviava — uma
  decisão de produto, não de refatoração.

## Próximos passos recomendados

1. **Migrations** (Alembic/Flask-Migrate). `create_all()` só cria tabelas
   ausentes: nunca altera colunas.
2. **`DateTime(timezone=True)`** no schema, com migration de dados. Hoje
   `infrastructure/clock.py` normaliza para naive-UTC para manter a
   compatibilidade.
3. **Refresh token** e revogação. O access token atual não tem contrapartida
   de renovação.
4. **Persistir notificações** numa tabela, em vez do estado em memória que
   foi removido.
