# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.
Refatorada para MVC com camadas de service e repository.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Nenhum segredo está no código. Copie `.env.example` e exporte as variáveis que
quiser sobrescrever:

| Variável | Default | Descrição |
| --- | --- | --- |
| `APP_ENV` | `development` | `development` ou `production` |
| `SECRET_KEY` | efêmera em dev | **Obrigatória** quando `APP_ENV=production` |
| `APP_DEBUG` | `true` em dev, `false` em prod | Modo debug do Flask |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | Bind do servidor de desenvolvimento |
| `DATABASE_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `BOOTSTRAP_DATABASE` | `true` em dev | Cria as tabelas no boot |
| `SEED_DATABASE` | `true` em dev | Insere dados de exemplo em banco vazio |
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula. Vazio desabilita CORS |

## Estrutura

```
app.py                              entry point (arranque do servidor)
src/
├── app.py                          composition root
├── container.py                    composição das dependências por requisição
├── exceptions.py                   erros de domínio (sem HTTP)
├── config/settings.py              configuração lida do ambiente
├── infrastructure/
│   ├── database.py                 conexão por requisição + transação explícita
│   └── schema.py                   bootstrap de schema e dados de exemplo
├── models/                         entidades e invariantes de domínio
│   ├── produto.py  usuario.py  pedido.py  relatorio.py
├── repositories/                   acesso a dados (SQL parametrizado)
│   ├── produto_repository.py  usuario_repository.py  pedido_repository.py
├── services/                       casos de uso e orquestração
│   ├── produto_service.py  usuario_service.py  pedido_service.py
│   ├── relatorio_service.py  health_service.py  notificacao_service.py
├── validators/produto_validator.py validação de forma da requisição
├── controllers/                    entrada HTTP, delegação e escolha da resposta
│   ├── produto_controller.py  usuario_controller.py  pedido_controller.py
│   ├── relatorio_controller.py  health_controller.py  requests.py
├── views/
│   ├── routes.py                   roteamento (blueprints)
│   ├── serializers.py              contratos de resposta
│   └── responses.py                envelope da API
└── middlewares/error_handler.py    tratamento centralizado de erros
```

## Validação

```bash
python validate_endpoints.py
```

Exercita todas as rotas originais conferindo status code, formato de resposta e
mensagens de erro, além dos casos de rollback e de injeção de SQL.

## Autenticação

As senhas são armazenadas com hash (`werkzeug.security`) e verificadas em
memória. O endpoint `GET /usuarios` não expõe o campo `senha`. Os usuários de
exemplo continuam com as mesmas senhas (`admin123`, `123456`, `senha123`), agora
gravadas como hash pelo seed — um `loja.db` criado antes da refatoração precisa
ser removido para que o seed rode novamente.
