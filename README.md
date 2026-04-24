# PRD v4.0 — SQUAD FISC
**Sistema Fiscal, Financeiro e Estoque Integrado**

> Versão: 4.0 | Status: Em Execução | Última revisão: Abril/2026

---

## SUMÁRIO

1. Visão Geral
2. Problema de Negócio
3. Objetivos do Produto
4. Público-Alvo / Personas
5. Escopo do Produto
6. Stack Tecnológica
7. Arquitetura Técnica
8. Fluxo Principal do Sistema
9. Modelo de Dados
10. Roadmap — Sprint 1: PRD e MVP do Banco de Dados
11. Roadmap — Sprint 2: Sistema Base e Módulos Core
12. Roadmap — Sprint 3: Telas, Dashboard, Regras e UX
13. Roadmap — Sprint 4: Integração Total e Infraestrutura
14. Roadmap — Sprint 5: Entrega Final
15. Requisitos Não-Funcionais
16. Segurança
17. Métricas de Sucesso
18. Riscos e Mitigações
19. Definição de Pronto (DoD Geral)
20. Futuro do Produto

---

## 1. VISÃO GERAL

O Squad FISC é responsável pelo desenvolvimento de um sistema ERP desktop voltado para pequenas e médias empresas brasileiras. O sistema centraliza operações críticas de gestão fiscal, controle de estoque e controle financeiro em uma única plataforma de uso local, desenvolvida em Python com interface gráfica nativa.

---

## 2. PROBLEMA DE NEGÓCIO

Empresas menores costumam operar com:

- Planilhas manuais sem integração entre setores
- Estoque sem rastreabilidade em tempo real
- Caixa descentralizado e difícil de auditar
- Impostos calculados manualmente com risco de erro fiscal
- Falta de indicadores para tomada de decisão

**Consequências diretas:**
- Erros operacionais e retrabalho
- Perdas financeiras por vendas sem estoque
- Risco de autuação fiscal
- Baixa produtividade do time

---

## 3. OBJETIVOS DO PRODUTO

Criar uma plataforma desktop única capaz de:

- Cadastrar e gerenciar produtos com alíquotas fiscais
- Controlar estoque em tempo real com rastreabilidade total
- Calcular impostos automaticamente
- Registrar e visualizar fluxo de caixa
- Controlar acessos por perfil de usuário (RBAC)
- Integrar com outros squads do ERP
- Entregar indicadores gerenciais em dashboard local

---

## 4. PÚBLICO-ALVO / PERSONAS

| Persona | Necessidade Principal |
|---|---|
| **Dono / Gestor** | Visualizar números, saldo, indicadores e relatórios |
| **Estoquista** | Registrar entradas e saídas de produtos rapidamente |
| **Contador** | Consultar notas, alíquotas e resumos fiscais |
| **Vendedor** | Gerar intenção de nota e confirmar venda com segurança |
| **Administrador** | Gerenciar usuários, perfis e permissões de acesso |

---

## 5. ESCOPO DO PRODUTO

**Inclui:**
- Aplicação desktop Python/PyQt6
- Banco de dados SQLite local
- Motor fiscal PHP via subprocess
- Autenticação local com hash de senha
- RBAC por perfil de usuário
- Dashboard com indicadores locais
- Relatórios exportáveis (CSV/TXT)
- Alertas de estoque mínimo
- Integração com outros squads via chamadas de módulo

**Não inclui neste momento:**
- Aplicativo mobile
- Plataforma web ou API REST pública
- Integração bancária real
- Suporte multi-empresa
- Emissão fiscal oficial junto à SEFAZ em produção
- Containerização Docker
- Deploy em servidor remoto

---

## 6. STACK TECNOLÓGICA

### Protótipo Atual

| Componente | Tecnologia |
|---|---|
| Linguagem principal | Python 3.12 |
| Interface gráfica | PyQt6 >= 6.6.0 |
| Banco de dados | SQLite (`app.db`) |
| Motor fiscal | PHP via subprocess (`backend_calculos.php`) |
| Acesso ao banco | `database.py` customizado |
| Instalação | `requirements.txt` + `instalar_dependencias.bat` |
| Execução | `run_app.bat` (Windows) |
| Empacotamento | PyInstaller via `gerar_executavel.bat` |
| UI Design | Qt Designer (`tela_principal.ui`) |
| Versionamento | Git + GitHub |
| Gestão de tarefas | Plane / OpenProject |

### Versão Evoluída

| Componente | Tecnologia |
|---|---|
| Integração entre módulos | Chamadas diretas Python |
| Banco de dados | SQLite com schema versionado |
| Testes | pytest |
| Documentação | README.md + docstrings |

---

## 7. ARQUITETURA TÉCNICA

```
Camada de Interface (PyQt6)
   ↓
Camada de Lógica de Negócio (Python)
   ├── Módulo Produtos
   ├── Módulo Estoque
   ├── Módulo Fiscal ←→ backend_calculos.php (subprocess)
   ├── Módulo Caixa
   ├── Módulo Auth
   └── Módulo RBAC
   ↓
Camada de Dados (SQLite via database.py)
   ↓
app.db (arquivo local)

Integrações:
↔ Squad 1 (Auth)
↔ Squad 3 (CRM)
↔ Squad 4 (Service Desk)
```

---

## 8. FLUXO PRINCIPAL DO SISTEMA

```
Login do Usuário
  ↓
Cadastrar Produto
  ↓
Registrar Entrada de Estoque
  ↓
Gerar Intenção de Nota / Calcular Impostos
  ↓
Confirmar Nota → Baixar Estoque + Registrar Receita no Caixa
  ↓
Consultar Saldo / Extrato
  ↓
Visualizar Dashboard
```

---

## 9. MODELO DE DADOS

```sql
-- Usuários e autenticação
CREATE TABLE usuarios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT NOT NULL,
    usuario        TEXT UNIQUE NOT NULL,
    senha_hash     TEXT NOT NULL,
    role           TEXT NOT NULL DEFAULT 'vendedor',
    ativo          INTEGER DEFAULT 1,
    primeiro_login INTEGER DEFAULT 1,
    criado_em      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Catálogo de produtos
CREATE TABLE produtos (
    sku              TEXT PRIMARY KEY,
    nome             TEXT NOT NULL,
    preco_base       DECIMAL(10,2) NOT NULL,
    aliquota_imposto DECIMAL(5,4) NOT NULL,
    estoque_minimo   INTEGER DEFAULT 0,
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Movimentações de estoque
CREATE TABLE estoque_mov (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sku        TEXT NOT NULL REFERENCES produtos(sku),
    tipo       TEXT NOT NULL CHECK(tipo IN ('entrada','saida','estorno')),
    quantidade INTEGER NOT NULL,
    motivo     TEXT,
    nota_id    INTEGER REFERENCES notas(id),
    criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Notas fiscais
CREATE TABLE notas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    status        TEXT NOT NULL CHECK(status IN ('rascunho','confirmada')),
    total_bruto   DECIMAL(10,2) NOT NULL,
    total_imposto DECIMAL(10,2) NOT NULL,
    total_final   DECIMAL(10,2) NOT NULL,
    usuario_id    INTEGER REFERENCES usuarios(id),
    criado_em     DATETIME DEFAULT CURRENT_TIMESTAMP,
    confirmado_em DATETIME
);

-- Itens da nota
CREATE TABLE itens_nota (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nota_id          INTEGER NOT NULL REFERENCES notas(id),
    sku              TEXT NOT NULL REFERENCES produtos(sku),
    quantidade       INTEGER NOT NULL,
    preco_base       DECIMAL(10,2) NOT NULL,
    aliquota_imposto DECIMAL(5,4) NOT NULL,
    imposto_item     DECIMAL(10,2) NOT NULL,
    total_item       DECIMAL(10,2) NOT NULL
);

-- Transações financeiras
CREATE TABLE transacoes_caixa (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT NOT NULL CHECK(tipo IN ('entrada','despesa','estorno')),
    descricao     TEXT NOT NULL,
    valor_bruto   DECIMAL(10,2) NOT NULL,
    valor_imposto DECIMAL(10,2) DEFAULT 0,
    valor_liquido DECIMAL(10,2) NOT NULL,
    nota_id       INTEGER REFERENCES notas(id),
    usuario_id    INTEGER REFERENCES usuarios(id),
    criado_em     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alertas
CREATE TABLE alertas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo      TEXT NOT NULL,
    mensagem  TEXT NOT NULL,
    lido      INTEGER DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Logs de auditoria
CREATE TABLE logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    acao       TEXT NOT NULL,
    tabela     TEXT,
    registro_id TEXT,
    detalhes   TEXT,
    criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 10. SPRINT 1 — PRD e MVP do Banco de Dados

**Objetivo:** Definir o produto, modelar o banco de dados inicial e entregar um protótipo desktop funcional como prova de conceito.

**Status:** ✅ Concluída

### Entregas

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-2 | Criação do PRD (FISC) | ✅ Done |
| FISCFISCAL-3 | MVP de Banco de Dados — Modelagem (ERD) | ✅ Done |

### Backlog de Requisitos Funcionais (base para sprints seguintes)

Levantados nesta sprint e implementados nas próximas:

**FISC-MOD1 — Cadastro de Produtos**
| ID | Requisito |
|---|---|
| FISCFISCAL-4 | RF01 — Criar Produto |
| FISCFISCAL-8 | RF02 — Listar produtos |
| FISCFISCAL-9 | RF03 — Buscar produto |
| FISCFISCAL-10 | RF04 — Editar produto |
| FISCFISCAL-11 | RF05 — Remover produto |
| FISCFISCAL-5 | RF06 — Validar SKU único |

**FISC-MOD2 — Controle de Estoque**
| ID | Requisito |
|---|---|
| FISCFISCAL-6 | RF01 — Registrar entrada |
| FISCFISCAL-12 | RF02 — Registrar saída |
| FISCFISCAL-7 | RF03 — Bloquear saída negativa |
| FISCFISCAL-13 | RF04 — Consultar saldo |
| FISCFISCAL-14 | RF05 — Histórico de movimentações |
| FISCFISCAL-15 | RF06 — Registrar motivo |

**FISC-MOD3 — Calculadora Fiscal**
| ID | Requisito |
|---|---|
| FISCFISCAL-16 | RF01 — Gerar intenção de nota |
| FISCFISCAL-17 | RF02 — Calcular imposto por item |
| FISCFISCAL-18 | RF03 — Calcular totais |
| FISCFISCAL-19 | RF04 — Validar SKUs |
| FISCFISCAL-20 | RF05 — Acionar baixa de estoque |

**FISC-MOD4 — Fluxo de Caixa**
| ID | Requisito |
|---|---|
| FISCFISCAL-21 | RF01 — Entrada automática |
| FISCFISCAL-22 | RF02 — Registrar despesa |
| FISCFISCAL-23 | RF03 — Consultar saldo |
| FISCFISCAL-24 | RF04 — Extrato por período |
| FISCFISCAL-25 | RF05 — Resumo financeiro |

---

## 11. SPRINT 2 — Sistema Base e Módulos Core

**Objetivo:** Implementar o backend completo com todos os módulos funcionais: autenticação, produtos, estoque, fiscal e caixa.

**Status:** ✅ Concluída

### MOD-S2-01 — Setup do Sistema

| ID | Task |
|---|---|
| FISCFISCAL-26 | FISC-MOD1 — Setup inicial do backend |
| FISCFISCAL-27 | FISC-MOD1 — Configurar estrutura de pastas |
| FISCFISCAL-28 | FISC-MOD1 — Configurar rotas base da API |

### MOD-S2-02 — Auth

| ID | Task |
|---|---|
| FISCFISCAL-29 | FISC-MOD2 — Criar endpoint de login |
| FISCFISCAL-30 | FISC-MOD2 — Implementar geração de JWT |
| FISCFISCAL-31 | FISC-MOD2 — Middleware de autenticação |
| FISCFISCAL-32 | FISC-MOD2 — Proteção de rotas privadas |

### MOD-S2-03 — Produtos

| ID | Task |
|---|---|
| FISCFISCAL-33 | FISC-MOD3 — Criar endpoint POST /products |
| FISCFISCAL-34 | FISC-MOD3 — Criar endpoint GET /products |
| FISCFISCAL-35 | FISC-MOD3 — Criar endpoint GET /products/{id} |
| FISCFISCAL-36 | FISC-MOD3 — Criar endpoint DELETE /products/{id} |
| FISCFISCAL-37 | FISC-MOD3 — Validação de SKU único |

### MOD-S2-04 — Estoque

| ID | Task |
|---|---|
| FISCFISCAL-38 | FISC-MOD4 — Endpoint entrada de estoque |
| FISCFISCAL-39 | FISC-MOD4 — Endpoint saída de estoque |
| FISCFISCAL-40 | FISC-MOD4 — Bloquear saída com saldo insuficiente |
| FISCFISCAL-41 | FISC-MOD4 — Endpoint consulta de saldo |
| FISCFISCAL-42 | FISC-MOD4 — Histórico de movimentações |
| FISCFISCAL-43 | FISC-MOD4 — Registro de motivo da movimentação |

### MOD-S2-05 — Fiscal

| ID | Task |
|---|---|
| FISCFISCAL-44 | FISC-MOD5 — Criar intenção de nota fiscal |
| FISCFISCAL-45 | FISC-MOD5 — Calcular imposto por item |
| FISCFISCAL-46 | FISC-MOD5 — Calcular totais da nota |
| FISCFISCAL-47 | FISC-MOD5 — Validar SKUs na nota |
| FISCFISCAL-48 | FISC-MOD5 — Baixa automática de estoque |

### MOD-S2-06 — Caixa

| ID | Task |
|---|---|
| FISCFISCAL-49 | FISC-MOD6 — Entrada automática no caixa |
| FISCFISCAL-50 | FISC-MOD6 — Registrar despesa manual |
| FISCFISCAL-51 | FISC-MOD6 — Consulta de saldo do caixa |
| FISCFISCAL-52 | FISC-MOD6 — Extrato por período |
| FISCFISCAL-53 | FISC-MOD6 — Resumo financeiro |

### MOD-S2-07 — Docs

| ID | Task |
|---|---|
| FISCFISCAL-54 | FISC-MOD7 — Documentar endpoints da API |
| FISCFISCAL-55 | FISC-MOD7 — Criar README do projeto |
| FISCFISCAL-56 | FISC-MOD7 — Organizar documentação técnica |

### MOD-S2-08 — Testes

| ID | Task |
|---|---|
| FISCFISCAL-57 | FISC-MOD8 — Testes unitários de produtos |
| FISCFISCAL-58 | FISC-MOD8 — Testes unitários de estoque |
| FISCFISCAL-59 | FISC-MOD8 — Testes unitários de fiscal |
| FISCFISCAL-60 | FISC-MOD8 — Testes unitários de caixa |

---

## 12. SPRINT 3 — Telas, Dashboard, Regras e UX

**Objetivo:** Construir todas as telas da interface desktop em PyQt6, implementar o dashboard, regras avançadas de negócio e as primeiras melhorias de UX.

**Status:** 🟡 Em andamento

### MOD-S3-01 — UX / Interface Desktop

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-61 | FISC-MOD1-01 — Padronizar paleta de cores e fontes em todas as telas | 🟡 In Progress |
| FISCFISCAL-62 | FISC-MOD1-02 — Implementar mensagens de feedback visual (sucesso, erro, alerta) | 🟡 In Progress |
| FISCFISCAL-63 | FISC-MOD1-03 — Adicionar confirmação antes de ações destrutivas (remover produto, cancelar nota) | 🟡 In Progress |
| FISCFISCAL-64 | FISC-MOD1-04 — Validação em tempo real nos campos de formulário (SKU, valores, datas) | 🟡 In Progress |

### MOD-S3-02 — Telas (Produtos / Estoque / Fiscal)

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-65 | FISC-MOD2-01 — Tela de listagem de produtos | 🟡 In Progress |
| FISCFISCAL-66 | FISC-MOD2-02 — Tela de criação de produto | 🟡 In Progress |
| FISCFISCAL-67 | FISC-MOD2-03 — Tela de edição de produto | 🟡 In Progress |
| FISCFISCAL-68 | FISC-MOD2-04 — Tela de entrada de estoque | 🟡 In Progress |
| FISCFISCAL-69 | FISC-MOD2-05 — Tela de saída de estoque | 🟡 In Progress |
| FISCFISCAL-70 | FISC-MOD2-06 — Tela de histórico | 🟡 In Progress |
| FISCFISCAL-71 | FISC-MOD2-07 — Tela de geração de nota | 🟡 In Progress |
| FISCFISCAL-72 | FISC-MOD2-08 — Tela de visualização de nota | 🟡 In Progress |

### MOD-S3-03 — API Pública

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-73 | FISC-MOD3-01 — Criar endpoints públicos | 🟡 In Progress |
| FISCFISCAL-74 | FISC-MOD3-02 — Documentar API pública | 🟡 In Progress |
| FISCFISCAL-75 | FISC-MOD3-03 — Padronizar respostas JSON | 🟡 In Progress |
| FISCFISCAL-76 | FISC-MOD3-04 — Controle de acesso básico | 🟡 In Progress |

### MOD-S3-04 — Dashboard

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-77 | FISC-MOD4-01 — Dashboard geral | 🟡 In Progress |
| FISCFISCAL-78 | FISC-MOD4-02 — Indicadores financeiros | 🟡 In Progress |
| FISCFISCAL-79 | FISC-MOD4-03 — Indicadores de estoque | 🟡 In Progress |
| FISCFISCAL-80 | FISC-MOD4-04 — Gráficos básicos | 🟡 In Progress |

### MOD-S3-05 — Regras Avançadas

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-81 | FISC-MOD5-01 — Validações avançadas de negócio | 🟡 In Progress |
| FISCFISCAL-82 | FISC-MOD5-02 — Tratamento de erros | 🟡 In Progress |
| FISCFISCAL-83 | FISC-MOD5-03 — Consistência de dados | 🟡 In Progress |
| FISCFISCAL-84 | FISC-MOD5-04 — Logs básicos | 🟡 In Progress |

### MOD-S3-06 — Integração Auth

| ID | Task | Status |
|---|---|---|
| FISCFISCAL-85 | FISC-MOD6-01 — Integração frontend com login | ✅ Done |
| FISCFISCAL-86 | FISC-MOD6-02 — Persistência de sessão | ✅ Done |
| FISCFISCAL-87 | FISC-MOD6-03 — Proteção de rotas frontend | ✅ Done |
| FISCFISCAL-88 | FISC-MOD6-04 — Logout | ✅ Done |

---

## 13. SPRINT 4 — Integração Total e Infraestrutura

**Objetivo:** Integrar o sistema com os outros squads do ERP, implementar RBAC completo, infraestrutura de ambiente e documentação técnica.

**Status:** 🔵 Backlog

### MOD-S4-01 — Integrações

| ID | Task |
|---|---|
| FISCFISCAL-89 | ISC-MOD4-01 — Teste de integração com Auth (Squad 1) |
| FISCFISCAL-90 | FISC-MOD4-02 — Integração com CRM (consulta de estoque) |
| FISCFISCAL-91 | FISC-MOD4-03 — Integração com Service Desk (histórico) |
| FISCFISCAL-92 | FISC-MOD4-04 — Teste end-to-end do ERP completo |

### MOD-S4-02 — Controle de Acesso (RBAC)

| ID | Task |
|---|---|
| FISCFISCAL-93 | FISC-MOD4-01 — Implementar RBAC em produtos |
| FISCFISCAL-94 | FISC-MOD4-02 — Implementar RBAC em estoque |
| FISCFISCAL-95 | FISC-MOD4-03 — Implementar RBAC em fiscal |
| FISCFISCAL-96 | FISC-MOD4-04 — Implementar RBAC em caixa |
| FISCFISCAL-97 | FISC-MOD4-05 — Tela de gestão de usuários |

### MOD-S4-03 — Testes

| ID | Task |
|---|---|
| FISCFISCAL-98 | FISC-MOD4-01 — Testes integração módulos core |
| FISCFISCAL-99 | FISC-MOD4-02 — Testes de segurança (auth e permissões) |
| FISCFISCAL-100 | FISC-MOD4-03 — Testes de regressão pós-integração |

### MOD-S4-04 — Deploy / Ambiente

| ID | Task |
|---|---|
| FISCFISCAL-101 | FISC-MOD4-01 — Configurar variáveis de ambiente (.env) |
| FISCFISCAL-102 | FISC-MOD4-02 — Criar Dockerfile |
| FISCFISCAL-103 | FISC-MOD4-03 — Configurar docker-compose |
| FISCFISCAL-104 | FISC-MOD4-04 — Preparar ambiente de execução |

### MOD-S4-05 — Documentação

| ID | Task |
|---|---|
| FISCFISCAL-105 | FISC-MOD4-01 — Atualizar README do projeto |
| FISCFISCAL-106 | FISC-MOD4-02 — Documentar arquitetura |
| FISCFISCAL-107 | FISC-MOD4-03 — Preparar pitch do Demoday |

### MOD-S4-06 — UX e Melhorias

| ID | Task |
|---|---|
| FISCFISCAL-108 | FISC-MOD4-01 — Implementar loading states |
| FISCFISCAL-109 | FISC-MOD4-02 — Feedback visual (toasts/erros) |
| FISCFISCAL-110 | FISC-MOD4-03 — Ajustar responsividade (tablet) |

---

## 14. SPRINT 5 — ENTREGA FINAL

**Objetivo:** Bug fix, qualidade, segurança, documentação final e apresentação no Demoday.

**Status:** 🔵 Backlog

### MOD-S5-01 — Bug Fix

| ID | Task |
|---|---|
| FISCFISCAL-111 | FISC-MOD5-01 — Levantamento e triagem de bugs |
| FISCFISCAL-112 | FISC-MOD5-02 — Correção de bugs críticos (P0) |
| FISCFISCAL-113 | FISC-MOD5-03 — Correção de bugs P1 |
| FISCFISCAL-114 | FISC-MOD5-04 — Ajustes finais de UX |

### MOD-S5-02 — Deploy

| ID | Task |
|---|---|
| FISCFISCAL-115 | FISC-MOD5-01 — Configurar servidor de produção |
| FISCFISCAL-116 | FISC-MOD5-02 — Deploy com Docker (docker-compose) |
| FISCFISCAL-117 | FISC-MOD5-03 — Verificar serviços (API, DB, frontend) |
| FISCFISCAL-118 | FISC-MOD5-04 — Configurar variáveis de ambiente |

### MOD-S5-03 — Segurança

| ID | Task |
|---|---|
| FISCFISCAL-119 | FISC-MOD5-01 — Configurar SSL (HTTPS) |
| FISCFISCAL-120 | FISC-MOD5-02 — Configurar variáveis seguras (JWT, DB) |
| FISCFISCAL-121 | FISC-MOD5-03 — Garantir proteção do .env |
| FISCFISCAL-122 | FISC-MOD5-04 — Testar ambiente de produção |

### MOD-S5-04 — Testes Finais

| ID | Task |
|---|---|
| FISCFISCAL-123 | FISC-MOD5-01 — Teste de login |
| FISCFISCAL-124 | FISC-MOD5-02 — Teste de criação de produto |
| FISCFISCAL-125 | FISC-MOD5-03 — Teste de entrada de estoque |
| FISCFISCAL-126 | FISC-MOD5-04 — Teste de geração de nota fiscal |
| FISCFISCAL-127 | FISC-MOD5-05 — Teste de confirmação de nota |
| FISCFISCAL-128 | FISC-MOD5-06 — Teste de atualização do caixa |

### MOD-S5-05 — Documentação Final

| ID | Task |
|---|---|
| FISCFISCAL-129 | FISC-MOD5-01 — Criar diagrama de arquitetura |
| FISCFISCAL-130 | FISC-MOD5-02 — Documentar decisões técnicas (ADR) |
| FISCFISCAL-131 | FISC-MOD5-03 — Atualizar Swagger/OpenAPI |
| FISCFISCAL-132 | FISC-MOD5-04 — Revisar documentação geral |

### MOD-S5-06 — Demoday

| ID | Task |
|---|---|
| FISCFISCAL-133 | FISC-MOD5-01 — Criar slides da apresentação |
| FISCFISCAL-134 | FISC-MOD5-02 — Definir roteiro da demo |
| FISCFISCAL-135 | FISC-MOD5-03 — Ensaiar apresentação |
| FISCFISCAL-136 | FISC-MOD5-04 — Preparar fallback (vídeo/demo gravada) |

### MOD-S5-07 — Opcional (SEFAZ)

| ID | Task |
|---|---|
| FISCFISCAL-137 | FISC-MOD5-01 — Estudar layout NFe |
| FISCFISCAL-138 | FISC-MOD5-02 — Gerar XML de nota fiscal |
| FISCFISCAL-139 | FISC-MOD5-03 — Validar XML com schema |
| FISCFISCAL-140 | FISC-MOD5-04 — Testar ambiente de homologação |

---

## 15. REQUISITOS NÃO-FUNCIONAIS

- Aplicação executa em Windows sem instalação adicional pelo usuário final (executável PyInstaller).
- Banco de dados SQLite local; não requer servidor de banco.
- Credenciais armazenadas com hash bcrypt; nunca em texto puro.
- Logs de auditoria registrados para todas as ações críticas.
- Interface responsiva a redimensionamento de janela (layouts PyQt6).
- Tempo de resposta de qualquer operação local inferior a 2 segundos.
- Código versionado em Git com branches por feature e PR obrigatório.

---

## 16. SEGURANÇA

- Senhas com hash bcrypt (nunca texto puro).
- Sessão mantida apenas em memória; não persiste em disco.
- RBAC aplicado em todas as funções críticas na camada Python.
- Logs de auditoria imutáveis para rastreabilidade.
- Transações SQLite com ROLLBACK em operações críticas.
- Subprocess PHP não aceita input não-sanitizado.
- Arquivo `.env` protegido e fora do repositório Git.

---

## 17. MÉTRICAS DE SUCESSO

- Fluxo completo funcional: cadastrar produto → estoque → nota → caixa → dashboard.
- Executável entregável rodando em Windows sem dependências extras.
- Integrações com outros squads ativas e testadas.
- Dashboard exibindo indicadores corretos.
- Testes automatizados cobrindo funções críticas de cada módulo.
- Demo ensaiada e estável para apresentação no Demoday.

---

## 18. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Atraso entre squads para integração | Alta | Alto | Contratos de integração definidos no Sprint 4 |
| Conflitos Git entre membros | Média | Médio | Branches por feature + PR obrigatório |
| Bugs no subprocess PHP | Média | Alto | Tratamento de erros + fallback de cálculo |
| Escopo excessivo na sprint | Alta | Médio | Priorização contínua no OpenProject |
| Executável PyInstaller com erro | Baixa | Alto | Testar empacotamento no Sprint 4 |
| Perda de dados SQLite | Baixa | Alto | Backup do `app.db` antes de cada uso |

---

## 19. DEFINIÇÃO DE PRONTO (DoD Geral)

- [ ] Produto cadastra, estoque é controlado, caixa atualiza e dashboard exibe dados corretos.
- [ ] Login funciona com RBAC aplicado em todos os módulos.
- [ ] Motor fiscal calcula corretamente e está integrado à interface.
- [ ] Todos os módulos com testes unitários nas funções críticas.
- [ ] Executável gerado e testado em máquina limpa.
- [ ] Documentação: README final, ADR e schema atualizado.
- [ ] Demo ensaiada com roteiro e fallback preparados.
- [ ] Repositório organizado com histórico de commits limpo.

---

## 20. FUTURO DO PRODUTO

- Emissão oficial de NF-e / NF-Se com integração SEFAZ.
- Versão web para acesso multi-dispositivo.
- Suporte multi-empresa.
- Integração bancária real para conciliação automática.
- BI avançado com gráficos históricos.
- App mobile companion para consulta de estoque e saldo.

---

*PRD v4.0 — Squad FISC | Abril/2026*
