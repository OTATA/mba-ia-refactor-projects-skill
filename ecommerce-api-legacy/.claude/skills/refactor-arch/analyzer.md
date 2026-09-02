# Analyzer

## Objetivo
Detectar stack, mapear arquitetura atual, imprimir resumo

Faca uma analise Heurística para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura

## Exemplo de saida

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

## Criterios de aceite
- Linguagem detectada corretamente
- Framework detectado corretamente
- Domínio da aplicação descrito corretamente
- Número de arquivos analisados condiz com a realidade