PRD — Squad FISC: Fiscal, Financeiro & Estoque
Emissão de NFe/NFSe · Fluxo de Caixa · Controle de Inventário

Versão: 1.0 · Sprint: 1 · Status: Em revisão · Data: 09/03/2026

---

Índice de Módulos
1. FISC-MOD1 — Cadastro de Produtos
2. FISC-MOD2 — Controle de Inventário (Estoque)
3. FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe
4. FISC-MOD4 — Fluxo de Caixa

---

## FISC-MOD1 — Cadastro de Produtos

### 1. Visão Geral e Proposta de Valor
Problema: Sem um catálogo centralizado ("Single Source of Truth"), o estoque opera às cegas sobre o preço, e o setor fiscal não sabe qual alíquota aplicar. O uso de planilhas paralelas entre setores gera inconsistência de dados, furos no caixa e erros na tributação.

Proposta de Valor: Centralizar os metadados de cada item (SKU, descrição, precificação e tributação) em um único registro imutável que alimenta automaticamente as operações de estoque e o motor de cálculo fiscal.

Oportunidade de Venda: Todo negócio físico precisa de um catálogo estruturado antes de operar. Como módulo isolado (SaaS), atua como um PIM (Product Information Management) básico. É o gatilho de entrada do cliente: sem ele, o sistema não fatura e não movimenta.

---

### 2. Personas
Lojista / Gerente de Operações: Responsável por manter o catálogo atualizado, definindo preços e cadastrando novos itens.

Estoquista: Consulta as especificações do produto (por nome ou SKU) antes de registrar movimentações físicas.

Contador / Analista Fiscal: Valida e audita as alíquotas de impostos atreladas a cada SKU para garantir conformidade legal.

---

### 3. Requisitos Funcionais (RF)
RF01: Criação de Produto: O sistema deve permitir o cadastro de um novo produto exigindo SKU (alfanumérico, único), Nome, Preço Base (monetário, > 0) e Alíquota de Imposto (percentual, 0 a 100).

RF02: Listagem Paginada: O sistema deve exibir o catálogo de produtos com suporte a paginação (ex: 50 itens por página) e ordenação.

RF03: Busca Dinâmica: Deve ser possível localizar um produto através de uma busca por correspondência exata de SKU ou correspondência parcial de Nome.

RF04: Edição Restrita: O sistema deve permitir a alteração de Nome, Preço Base e Alíquota. O campo SKU atua como chave de negócio e não pode ser alterado após a criação.

RF05: Deleção Lógica (Soft Delete) e Validação: O sistema só pode inativar/remover um produto se o módulo de Estoque (MOD2) confirmar que não há movimentações atreladas a ele. Produtos recém-cadastrados iniciam com saldo de estoque igual a 0.

RF06: Prevenção de Duplicidade: Rejeitar a criação de produtos com um SKU já existente no mesmo Tenant, retornando erro claro ao usuário.

---

### 4. Requisitos Não-Funcionais (RNF)
Segurança (Isolamento multitenant): Todas as consultas e gravações devem obrigatoriamente filtrar pelo tenant_id (ID da empresa) extraído do token JWT gerado pelo [CORE]. Um cliente nunca pode ver o produto de outro.

Integridade (Database): O campo SKU deve ter uma restrição de UNIQUE INDEX no banco de dados, combinada com o tenant_id.

Performance: A listagem e a busca de produtos (até 10.000 registros) devem retornar os dados na API em menos de 200ms (p95).

Escalabilidade: O banco de dados deve estar preparado para alto volume de leituras, permitindo futura implementação de cache (ex: Redis) para SKUs muito acessados pelo módulo Fiscal.

---

### 5. Especificação Técnica e Integração Endpoints de API (RESTful):

POST /v1/fisc/products (Retorna 201 Created)

GET /v1/fisc/products?page=1&limit=50 (Retorna 200 OK)

GET /v1/fisc/products/{sku} (Retorna 200 OK ou 404 Not Found)

PUT /v1/fisc/products/{sku} (Retorna 200 OK)

DELETE /v1/fisc/products/{sku} (Retorna 204 No Content ou 409 Conflict se houver estoque)

Webhooks / Eventos Disparados:

product.created: Notifica criação. Consumidores: MOD2 (iniciar ledger de saldo zerado).

product.updated: Notifica alteração de preço/imposto. Consumidores: MOD3 (atualizar regras futuras).

product.deleted: Notifica inativação. Consumidores: MOD2.

Diagrama de Dados (JSON Payload):

JSON

{
  "sku": "CAN-AZUL-001",
  "nome": "Caneta Azul BIC",
  "preco_base": 2.50,
  "aliquota_imposto": 12.00,
  "status": "active",
  "created_at": "2026-03-09T10:00:00Z"
}

---

### 6. User Stories

"Como Lojista, eu quero cadastrar produtos para organizar meu catálogo e garantir que estoque e fiscal usem sempre as mesmas informações."

"Como Contador, eu quero consultar a alíquota de imposto de cada produto para validar os cálculos fiscais sem depender de planilhas paralelas."

---

### 7. Critérios de Aceite

- É possível criar produto com SKU, Nome, Preço Base e Alíquota.
- SKU duplicado é rejeitado com mensagem de erro.
- É possível listar, editar e remover produtos.
- Produto com movimentações de estoque não pode ser removido.
- Produto recém-cadastrado inicia com saldo de estoque = 0.

---

### 8. Definição de Pronto (DoD)

- Código revisado por outro membro do Squad.
- Testes unitários com >80% de cobertura.
- Documentação da API atualizada (Swagger/OpenAPI).
- Pipeline de CI/CD passando.
- Webhooks validados por MOD2 e MOD3.

---

## FISC-MOD2 — Controle de Inventário (Estoque)

### 1. Visão Geral e Proposta de Valor

Problema: Sem controle de estoque em tempo real, vendas são confirmadas sem produto disponível ou produtos ficam parados por excesso sem que ninguém perceba.

Proposta de Valor: Registrar cada entrada e saída de produto em tempo real, mantendo o saldo correto e impedindo vendas de itens indisponíveis.

---

### 2. Personas

- Estoquista: Registrar entradas (compras/devoluções) e saídas (vendas).
- Lojista / Gerente: Consultar saldo atual e histórico de movimentações.
- Sistema Fiscal (interno): Acionar saída de estoque ao confirmar uma venda.

---

### 3. Requisitos Funcionais (RF)

- RF01 Registrar entrada: Adicionar X unidades ao estoque de um produto, informando SKU e quantidade.
- RF02 Registrar saída: Retirar X unidades do estoque informando SKU e quantidade.
- RF03 Bloquear saída negativa: Rejeitar saída maior que o saldo disponível com mensagem: "Estoque insuficiente. Saldo atual: X."
- RF04 Consultar saldo: Exibir a quantidade disponível de um produto pelo SKU.
- RF05 Histórico: Exibir todas as movimentações de um produto com data, hora, quantidade e tipo.
- RF06 Registrar motivo: Permitir informar motivo da movimentação (ex: venda, devolução, ajuste).

---

### 4. Requisitos Não-Funcionais (RNF)

- RNF01 Atomicidade: Saída de estoque e confirmação de venda ocorrem juntas. Se a venda falhar, o estoque não é alterado.
- RNF02 Rastreabilidade: Movimentações são imutáveis após registro — correções via estorno.
- RNF03 Performance: Consulta de saldo deve responder em menos de 300ms.
- RNF04 Escalabilidade: Operações de entrada/saída usam lock otimista por SKU para evitar condição de corrida.

---

### 5. Especificação Técnica e Integração

Endpoints de API

POST /v1/fisc/stock/entry -> Registra entrada
POST /v1/fisc/stock/exit -> Registra saída
GET /v1/fisc/stock/{sku} -> Consulta saldo
GET /v1/fisc/stock/{sku}/history -> Histórico do produto

Webhooks disparados por este módulo
- stock.entry_registered: Payload { sku, quantidade, saldo_atual, motivo }. Consumidor: MOD4 (Fluxo de Caixa, se compra).
- stock.exit_registered: Payload { sku, quantidade, saldo_atual, nota_id }. Consumidor: MOD3 (confirmação de baixa).
- stock.insufficient: Payload { sku, saldo_atual, quantidade_solicitada }. Consumidor: MOD3 (para bloquear nota).

---

### 6. User Stories

"Como Estoquista, eu quero registrar entradas e saídas de produtos para manter o inventário atualizado em tempo real."

"Como Lojista, eu quero consultar o histórico de movimentações de um produto para entender o que aconteceu com o meu estoque."

---

### 7. Critérios de Aceite

- É possível registrar ENTRADA de X unidades por SKU.
- É possível registrar SAÍDA de X unidades por SKU.
- Saída maior que o saldo é bloqueada com mensagem de erro.
- Saldo é atualizado imediatamente após cada movimentação.

---

## FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe

### 1. Visão Geral e Proposta de Valor

Problema: Calcular impostos manualmente por venda é lento e sujeito a erro, gerando riscos de autuação fiscal.

Proposta de Valor: Dado um conjunto de produtos/serviços vendidos, o módulo calcula automaticamente os impostos e gera um objeto estruturado (JSON) representando a "intenção de nota fiscal".

Escopo: O módulo gera o objeto de dados fiscal calculado. A emissão real junto à SEFAZ / Prefeitura é escopo de versões futuras.

---

### 2. Requisitos Funcionais (RF)

- RF01 Gerar intenção de nota: Recebe lista de itens (SKU + quantidade) e retorna o JSON completo da nota.
- RF02 Calcular imposto por item: Fórmula: imposto = preco_base × aliquota_imposto × quantidade.
- RF03 Calcular totais: Soma valor bruto total, imposto total e valor final total da nota.
- RF04 Validar SKUs: Retorna erro identificando qualquer SKU não encontrado no cadastro.
- RF05 Acionar baixa de estoque: Ao confirmar a nota, solicita saída de estoque para todos os itens (atomicidade com MOD2).

---

### 3. Especificação Técnica e Integração

Endpoints de API
POST /v1/fisc/invoice/intent -> Gera intenção de nota fiscal
GET /v1/fisc/invoice/{id} -> Consulta nota por ID

Webhooks disparados por este módulo
- invoice.generated: Payload { id, total_bruto, total_imposto, total_final, data_emissao }. Consumidores: MOD2 (baixa de estoque), MOD4 (entrada financeira).

---

## FISC-MOD4 — Fluxo de Caixa

### 1. Visão Geral e Proposta de Valor

Problema: Sem controle financeiro centralizado, o empresário não sabe se a empresa está lucrando.

Proposta de Valor: Registrar automaticamente cada transação financeira vinculada à nota fiscal gerada e permitir visualizar saldo e extrato do período.

---

### 2. Requisitos Funcionais (RF)

- RF01 Entrada automática: Toda nota confirmada gera entrada com valor bruto, imposto, valor líquido e data/hora.
- RF02 Registrar despesa: Registrar saída financeira manual com descrição, valor e data.
- RF03 Consultar saldo: Calcular e exibir saldo atual: entradas − saídas.
- RF04 Extrato por período: Listar todas as transações dentro de um intervalo de datas.
- RF05 Resumo financeiro: Exibir total de entradas, saídas, impostos e saldo líquido.

---

### 3. Especificação Técnica e Integração

Endpoints de API
POST /v1/fisc/cashflow/entry -> Registra entrada financeira
POST /v1/fisc/cashflow/expense -> Registra despesa/saída
GET /v1/fisc/cashflow/balance -> Consulta saldo atual
GET /v1/fisc/cashflow/statement -> Extrato (?from=&to=)

---

### 4. Definição de Pronto (DoD) Geral

- Código revisado por outro membro do Squad.
- Testes unitários com >80% de cobertura.
- Documentação da API atualizada (Swagger/OpenAPI).
- Pipeline de CI/CD passando.
- Integração entre módulos (MOD2, MOD3, MOD4) validada end-to-end.
