# PRD v2.0 COMPLETO — SQUAD FISC

Sistema Fiscal, Financeiro e Estoque Integrado

Versão: 2.0
Status: Planejado + Em Execução
Última revisão: Abril/2026

---

# 1. VISÃO GERAL

O Squad FISC é responsável pelo desenvolvimento do módulo ERP voltado para:

* Gestão fiscal
* Controle financeiro
* Controle de estoque
* Integrações empresariais
* Dashboard gerencial
* API pública

O sistema foi idealizado para pequenas e médias empresas que precisam centralizar operações críticas em uma única plataforma.

---

# 2. PROBLEMA DE NEGÓCIO

Empresas menores costumam operar com:

* planilhas manuais
* estoque sem rastreabilidade
* caixa descentralizado
* impostos calculados manualmente
* falta de indicadores

Consequências:

* erros operacionais
* perda financeira
* vendas sem estoque
* risco fiscal
* baixa produtividade

---

# 3. OBJETIVOS DO PRODUTO

Criar uma plataforma única capaz de:

* cadastrar produtos
* controlar estoque em tempo real
* gerar cálculos fiscais
* registrar fluxo de caixa
* controlar usuários
* integrar com outros sistemas
* entregar indicadores gerenciais

---

# 4. PÚBLICO-ALVO / PERSONAS

## Dono / Gestor

Precisa enxergar números e operação.

## Estoquista

Precisa movimentar estoque rapidamente.

## Contador

Precisa consultar notas e impostos.

## Vendedor

Precisa vender com segurança e gerar documentos.

## Administrador

Precisa controlar acessos e usuários.

---

# 5. ESCOPO DO PRODUTO

Inclui:

* backend API REST
* frontend web
* autenticação JWT
* RBAC
* documentação Swagger
* deploy containerizado
* integração multi-squad

Não inclui inicialmente:

* app mobile
* integração bancária real
* multiempresa
* emissão fiscal oficial em produção

---

# 6. MÓDULOS DO SISTEMA

| Código     | Nome                 |
| ---------- | -------------------- |
| FISC-MOD1  | Cadastro de Produtos |
| FISC-MOD2  | Controle de Estoque  |
| FISC-MOD3  | Fiscal / Nota        |
| FISC-MOD4  | Fluxo de Caixa       |
| FISC-MOD5  | Autenticação         |
| FISC-MOD6  | Interface Web        |
| FISC-MOD7  | API Pública          |
| FISC-MOD8  | Dashboard            |
| FISC-MOD9  | Integração SEFAZ     |
| FISC-MOD10 | RBAC                 |

---

# 7. ARQUITETURA TÉCNICA

```text
Frontend Web
   ↓
API REST Squad FISC
   ↓
Banco de Dados

Integrações:
↔ Squad 1 (Auth)
↔ Squad 3 (CRM)
↔ Squad 4 (Service Desk)
```

---

# 8. STACK TECNOLÓGICA

## Protótipo Inicial

* Python
* PyQt6
* SQLite
* PHP (motor fiscal)

## Versão Evoluída

* Backend REST
* MySQL/PostgreSQL
* Frontend Web
* JWT
* Docker
* Swagger/OpenAPI
* GitHub
* Plane
* OpenProject

---

# 9. FLUXO PRINCIPAL DO SISTEMA

```text
Cadastrar Produto
↓
Entrada de Estoque
↓
Venda
↓
Gerar Nota
↓
Baixar Estoque
↓
Registrar Entrada Financeira
↓
Atualizar Dashboard
```

---

# 10. REQUISITOS FUNCIONAIS

## Produtos

* criar produto
* editar produto
* excluir produto
* listar produtos
* buscar por SKU

## Estoque

* entrada
* saída
* saldo atual
* histórico
* estoque mínimo

## Fiscal

* cálculo de impostos
* nota provisória
* confirmar nota
* consultar nota

## Caixa

* registrar entrada
* registrar despesa
* saldo líquido
* extrato

## Auth

* login
* logout
* sessão
* roles

## Dashboard

* saldo
* gráficos
* indicadores

---

# 11. REQUISITOS NÃO FUNCIONAIS

* API JSON padronizada
* autenticação JWT
* RBAC
* logs
* performance adequada
* segurança de credenciais
* dockerização
* versionamento Git
* documentação técnica

---

# 12. ROADMAP COMPLETO DE SPRINTS

---

# SPRINT 01 — FUNDAÇÃO

Objetivo:

* PRD inicial
* banco MVP
* repositório
* protótipo desktop

Entregas:

* schema inicial
* README
* estrutura Git
* Plane configurado
* prova de conceito funcional

---

# SPRINT 02 — BACKEND / APIs CORE

## MOD-S2-01 — Setup API

* FISC-MOD1-01 Setup arquitetura
* FISC-MOD1-02 Migração schema
* FISC-MOD1-03 Middleware JSON

## MOD-S2-02 — Auth

* Login JWT
* Guard de rotas
* Usuários seed
* Logout

## MOD-S2-03 — Produtos

* Criar produto
* Listar produtos
* Buscar produto
* Editar produto
* Excluir produto

## MOD-S2-04 — Estoque

* Entrada
* Saída
* Histórico
* Saldo

## MOD-S2-05 — Fiscal

* Intent nota
* Confirmar nota
* Consultar nota

## MOD-S2-06 — Caixa

* Despesa manual
* Saldo atual
* Extrato

## MOD-S2-07 — Docs

* README_API
* Postman

## MOD-S2-08 — Testes

* Unitários
* Integração

---

# SPRINT 03 — FRONTEND + API PÚBLICA

## MOD-S3-01 — Frontend Base

* Setup frontend
* Estrutura pastas
* Rotas
* HTTP client

## MOD-S3-02 — Telas

Produtos:

* listagem
* criação
* edição

Estoque:

* entrada
* saída
* histórico

Fiscal:

* geração nota
* visualização nota

Caixa:

* saldo
* extrato

## MOD-S3-03 — API Pública

* endpoints públicos
* swagger
* API Key

## MOD-S3-04 — Dashboard

* indicadores financeiros
* indicadores estoque
* gráficos

## MOD-S3-05 — Regras avançadas

* alerta estoque
* estorno
* consistência
* logs

## MOD-S3-06 — Integração Auth

* login externo
* sessão
* tokens

---

# SPRINT 04 — INTEGRAÇÃO TOTAL

## MOD-S4-01 — Integrações

* Squad 1 Auth
* Squad 3 CRM
* Squad 4 Service Desk
* teste ERP completo

## MOD-S4-02 — RBAC

* permissões produtos
* permissões estoque
* permissões fiscal
* permissões caixa
* tela usuários

## MOD-S4-03 — Testes

* regressão
* segurança
* integração

## MOD-S4-04 — Infra

* .env
* Dockerfile
* docker-compose
* ambiente execução

## MOD-S4-05 — Docs

* README final
* pitch
* arquitetura

## MOD-S4-06 — UX

* loading
* feedback visual
* responsividade

---

# SPRINT 05 — ENTREGA FINAL

## MOD-S5-01 — Bug Fix

* triagem bugs
* correção P0
* correção P1
* refinos UX

## MOD-S5-02 — Deploy

* servidor
* docker produção
* SSL
* smoke test

## MOD-S5-03 — Docs finais

* arquitetura
* ADR
* Swagger final

## MOD-S5-04 — Demoday

* slides
* roteiro
* ensaio
* fallback

## MOD-S5-05 — Opcional

* estudo SEFAZ
* XML NFe
* homologação

---

# 13. ENDPOINTS PRINCIPAIS

## Auth

POST /auth/login
POST /auth/logout
GET /auth/me

## Produtos

POST /products
GET /products
GET /products/{id}
PUT /products/{id}
DELETE /products/{id}

## Estoque

POST /stock/entry
POST /stock/exit
GET /stock/{sku}

## Fiscal

POST /invoice/intent
POST /invoice/confirm
GET /invoice/{id}

## Caixa

POST /cashflow/expense
GET /cashflow/balance
GET /cashflow/statement

---

# 14. MODELO DE DADOS

## Tabelas principais

* usuarios
* produtos
* estoque_mov
* notas
* itens_nota
* transacoes_caixa
* logs
* alerts

---

# 15. SEGURANÇA

* JWT
* senha hash bcrypt
* RBAC
* .env protegido
* HTTPS
* validação input
* prevenção SQL injection

---

# 16. INTEGRAÇÕES EXTERNAS

* Squad 1 → autenticação
* Squad 3 → CRM / vendas
* Squad 4 → atendimento
* Squad 5 → DevOps (apoio deploy)

---

# 17. MÉTRICAS DE SUCESSO

* fluxo completo funcional
* deploy online
* integrações ativas
* dashboard pronto
* testes automatizados
* apresentação estável

---

# 18. RISCOS DO PROJETO

* atraso entre squads
* conflitos Git
* bugs integração
* escopo excessivo
* falta de ambiente deploy

Mitigação:

* branches
* PR review
* priorização sprint
* smoke tests

---

# 19. FUTURO DO PRODUTO

* app mobile
* multiempresa
* NF-e oficial
* integração bancária
* BI avançado
* emissão automática

---

# 20. DEFINIÇÃO FINAL DE PRONTO

* produto cadastra e vende
* estoque baixa corretamente
* caixa atualiza
* login funciona
* permissões ativas
* frontend completo
* documentação pronta
* deploy funcional
* demo ensaiada
* repositório organizado

