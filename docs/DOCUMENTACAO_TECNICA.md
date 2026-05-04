# Documentação Técnica e Arquitetura

## Visão Geral

O Fiscal Finance evoluiu para uma aplicação **Web (Client-Server)** desenvolvida para gestão empresarial acadêmica. Ela contém módulos integrados de produtos, estoque, fiscal, caixa e nota fiscal, com foco em uma arquitetura leve, moderna e descentralizada.

## Arquitetura do Sistema

A aplicação é dividida em um **Frontend** (Single Page Application) e um **Backend** (API RESTful).

```mermaid
flowchart TD
    subgraph Frontend [Frontend Web - SPA]
        UI[Interface do Usuário\nHTML5, CSS3, JS Vanilla]
        Fetch[Fetch API\nChamadas Assíncronas]
    end

    subgraph Backend [Backend - API REST]
        Flask[Flask App / Roteador]
        Auth[Módulo de Autenticação]
        Prod[Módulos de Negócios\n(Produtos, Estoque, Notas, Caixa)]
        DBLayer[database.py\nCamada de Acesso]
    end

    subgraph Data [Armazenamento]
        SQLite[(SQLite\napp.db)]
    end

    UI <-->|Interação| Fetch
    Fetch <-->|HTTP / JSON| Flask
    Flask --> Auth
    Flask --> Prod
    Auth --> DBLayer
    Prod --> DBLayer
    DBLayer <--> SQLite
```

## Stack Tecnológica

- **Backend:** Python 3, Flask, Flask-CORS
- **Banco de Dados:** SQLite embutido
- **Frontend:** HTML5, CSS3 (CSS Nativo), Vanilla JavaScript
- **Integração:** REST API consumida via `fetch`

## Estrutura do Projeto

- `backend/`
  Contém toda a lógica da API REST (rotas, validação de regras de negócios e cálculo fiscal).
  - `app.py`: Servidor principal e roteador Flask.
  - `database.py`: Gerenciamento da conexão com o SQLite.
  - Scripts modulares (`products.py`, `stock.py`, `invoice.py`, `cashflow.py`, `auth.py`).

- `frontend/`
  Apresentação e telas em páginas HTML separadas, estilizadas com a pasta `css/` e orquestradas pela pasta `js/`. Comunicação via requisições assíncronas (JSON).

- `data/`
  Armazena o banco de dados local `app.db`.

- `docs/`
  Contratos de API, documentações de endpoints e o diagrama de arquitetura.

## Fluxo Geral da Aplicação

1. **Autenticação:** O usuário loga na aplicação para acessar o Dashboard.
2. **Cadastros Base:** Cadastro de produtos (com precificação e SKUs).
3. **Estoque:** Movimentação de estoque de produtos (entradas e saídas).
4. **Operações Fiscais:** Simulação de cálculo fiscal e emissão de intenção de nota.
5. **Financeiro (Caixa):** As vendas e despesas alimentam automaticamente o fluxo de caixa.
6. **Métricas:** Dashboard em tempo real consumindo os micro-serviços do backend para apresentar a saúde do negócio.
