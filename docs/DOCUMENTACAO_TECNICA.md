# Documentação Técnica

## Visão Geral

Sistema desktop desenvolvido para gestão empresarial acadêmica, contendo módulos integrados de produtos, estoque, fiscal, caixa e nota fiscal.

## Stack Utilizada

- Python 3
- PyQt6
- SQLite
- PHP (motor fiscal)
- GitHub

## Estrutura do Projeto

- app.py  
Interface principal e regras de interação.

- database.py  
Camada de acesso ao banco de dados SQLite.

- backend_calculos.php  
Motor de cálculo tributário.

- tela_principal.ui  
Interface gráfica criada no Qt Designer.

- requirements.txt  
Dependências Python.

- run_app.bat  
Inicialização rápida no Windows.

## Banco de Dados

Tabelas principais:

- produtos
- estoque
- caixa
- notas_fiscais
- itens_nota

## Fluxo Geral

1. Cadastrar produto
2. Registrar estoque
3. Calcular operação fiscal
4. Emitir nota
5. Atualizar caixa

## Evolução Planejada

- API REST
- Autenticação JWT
- Dashboard web
- Relatórios avançados
- Deploy em nuvem
