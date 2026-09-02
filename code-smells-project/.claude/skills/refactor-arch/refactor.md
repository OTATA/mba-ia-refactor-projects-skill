# Refactor

## Objetivos
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças
- Endpoints originais respondem corretamente

## Use os catalogos com as diretrizes para a refatoracao 
Read `mvc.md`.
Read `playbook.md`.

## exemplo de saída
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================

## Criterios de aceite

- Estrutura de diretórios segue padrão MVC
- Configuração extraída para módulo de config (sem hardcoded)
- Models criados para abstrair dados
- Views/Routes separadas para roteamento
- Controllers concentram o fluxo da aplicação
- Error handling centralizado
- Entry point claro
- Aplicação inicia sem erros
- Endpoints originais respondem corretamente
