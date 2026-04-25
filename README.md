# Fiscal Finance — Squad FISC

Fiscal Finance é um sistema integrado de gestão voltado para as áreas Fiscal, Financeira e de Estoque. O projeto permite centralizar o controle operacional em uma única plataforma web, evitando a necessidade de planilhas paralelas e melhorando a integridade das informações entre setores.

## 🚀 Módulos Principais

1. **Cadastro de Produtos (FISC-MOD1)**: Repositório central com os SKUs, preços base e alíquotas de impostos, alimentando diretamente o estoque e a calculadora fiscal.
2. **Controle de Inventário (FISC-MOD2)**: Livro-razão (*Ledger*) do estoque para registrar entradas e saídas e garantir rastreabilidade imutável de movimentações.
3. **Fiscal e Notas (FISC-MOD3)**: Calculadora fiscal capaz de cruzar itens vendidos com suas alíquotas, computando o valor exato dos tributos (NFe/NFSe).
4. **Fluxo de Caixa (FISC-MOD4)**: Gestão consolidada de entradas (originadas de notas emitidas) e saídas manuais, gerando um extrato financeiro simplificado (DRE básico).

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python + Flask (API RESTful), SQLite.
- **Frontend:** Web nativa usando HTML5, CSS3 (com suporte a Dark Mode) e JavaScript Vanilla.
- **Integração:** Arquitetura desacoplada onde o frontend consome diretamente as rotas de API do backend.

## 📁 Estrutura de Diretórios

```
Fiscal-Finance/
├── backend/             # Código fonte da API (Flask, rotas, lógica de banco)
├── frontend/            # Interface gráfica web (HTML, CSS, JS)
├── docs/                # Documentações do projeto (PRD, API Contract, Endpoints, etc)
├── PROTOTIPO/           # Banco de dados e ferramentas antigas/protótipo (PyQt)
├── postman/             # Collections de teste para a API
└── run_web.bat          # Script prático para inicializar a aplicação no Windows
```

## ⚙️ Como Executar

A inicialização do projeto está automatizada. Para executar:

1. Certifique-se de que o **Python 3** está instalado na máquina.
2. Na raiz do projeto, dê um duplo clique no arquivo `run_web.bat`.

O script cuidará de:
- Instalar quaisquer dependências não encontradas (através de `backend/requirements.txt`).
- Iniciar o servidor de API Flask em segundo plano na porta 5000.
- Abrir automaticamente a interface no seu navegador padrão (`http://localhost:5000/`).

> **Nota para Desenvolvedores:** Caso prefira iniciar de forma manual, ative um ambiente virtual e rode `python app.py` dentro da pasta `backend/`. 

## 🔐 Autenticação e Perfis

O sistema possui autenticação JWT. No acesso web (via `index.html`), usuários podem ter as visões normais da operação ou visão de `admin` (que também desbloqueia o *API Tester* completo na lateral do painel).

## 📄 Documentação Completa

Para aprofundamento nas regras de negócios, contratos de API e demais informações do desenvolvimento:
- Leia os documentos detalhados contidos na pasta [`docs/`](./docs). O PRD (Product Requirements Document) original, a listagem de Endpoints e contratos públicos estão todos hospedados lá.
