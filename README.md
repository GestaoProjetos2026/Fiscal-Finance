# Fiscal Finance

Bem-vindo ao **Fiscal Finance**, um sistema web integrado para gerenciamento administrativo, desenvolvido para simplificar operações de lojas e pequenas empresas.

A aplicação fornece uma interface moderna e centralizada para gerenciar o ciclo de vida operacional, desde o cadastro do produto até a emissão da nota fiscal e o registro financeiro, tudo consumindo uma API REST robusta.

## 🚀 Funcionalidades

- **Dashboard:** Visão geral da operação com métricas consolidadas em tempo real.
- **Produtos:** Catálogo completo com controle de SKU, precificação e alíquotas de imposto.
- **Estoque:** Registro de entradas e saídas e acompanhamento de saldos dinâmico.
- **Fiscal:** Calculadora que cruza a venda de produtos com a alíquota cadastrada, gerando simulações exatas para Nota Fiscal.
- **Caixa:** Controle financeiro (extrato e saldo) integrado, registrando automaticamente as vendas e permitindo o lançamento manual de despesas.
- **API Tester:** Ferramenta embutida exclusiva para administradores testarem todos os endpoints do backend.

## 🛠️ Stack Tecnológica

- **Backend:** Python 3 + Flask. Servidor responsável pela lógica de negócios, cálculos fiscais e conexão com o banco.
- **Banco de Dados:** SQLite (leve e embutido no projeto).
- **Frontend:** Single Page Application (SPA) construída em HTML5, CSS3 nativo (com tema escuro profissional) e JavaScript puro (Vanilla JS), comunicando-se com a API via *fetch*.

## 📁 Estrutura do Projeto

```text
Fiscal-Finance/
├── backend/             # Lógica da API Flask (rotas, validações, banco de dados)
├── frontend/            # Toda a interface do usuário (Páginas, Scripts e Estilos)
├── docs/                # Documentação técnica e planejamento antigo do sistema
├── data/                # Arquivo do banco de dados local (app.db) e schemas
└── run_web.bat          # Inicializador automático do sistema
```

## ⚙️ Como Executar

O projeto já está configurado para rodar de maneira muito simples no Windows:

1. Dê um duplo-clique no arquivo `run_web.bat`.
2. O script vai automaticamente:
   - Instalar dependências necessárias (como o `flask` e `flask-cors`).
   - Subir o servidor da API.
   - Abrir o sistema no seu navegador (geralmente em `http://localhost:5000`).

### Login Padrão
Para testar, você pode usar os seguintes dados fictícios de acesso já cadastrados:
- **E-mail:** `admin@fiscal.com`
- **Senha:** `admin123`

## 📡 API e Integração

O backend foi projetado no padrão RESTful, o que significa que o frontend web atual e quaisquer outros sistemas futuros podem consumir as mesmas rotas. A documentação completa de rotas e o contrato de API estão disponíveis na pasta `docs/`.
