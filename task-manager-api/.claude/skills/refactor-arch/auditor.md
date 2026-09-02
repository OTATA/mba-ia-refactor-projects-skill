# Auditor

## Objetivo
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados

## Avalie os anti-patterns
Read `anti-patterns.md`.

### exemplo de saida

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

Findings

[CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL,
             validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

[CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

### Criterios de aceite
 - Cada finding tem arquivo e linhas exatos
 - Findings ordenados por severidade (CRITICAL → LOW)
 - Mínimo de 5 findings identificados

#### salve o report
 - suba para ../../../
 - salve dentro do diretório reports/
 - use o nome do projeto como o nome do arquivo, exemplo: projeto.md

