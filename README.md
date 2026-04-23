# PRD — Squad FISC: Fiscal, Financeiro & Estoque
**Produto:** Emissão de NFe/NFSe · Fluxo de Caixa · Controle de Inventário  
**Versão:** 1.0 · **Sprint:** 1 · **Status:** Em revisão · **Data:** 09/03/2026

---

## Índice de Módulos
1. FISC-MOD1 — Cadastro de Produtos
2. FISC-MOD2 — Controle de Inventário (Estoque)
3. FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe
4. FISC-MOD4 — Fluxo de Caixa

---

# FISC-MOD1 — Cadastro de Produtos

### 1. Visão Geral e Proposta de Valor
**Problema:** Sem um catálogo centralizado, o estoque opera às cegas sobre o preço e o setor fiscal não sabe qual alíquota aplicar. O uso de planilhas paralelas entre setores gera inconsistência de dados, furos no caixa e erros na tributação.  
**Proposta de Valor:** Centralizar os metadados de cada item (SKU, descrição, precificação e tributação) em um único registro imutável que alimenta automaticamente as operações de estoque e o motor de cálculo fiscal.  
**Oportunidade de Venda:** Todo negócio físico precisa de um catálogo estruturado antes de operar. Este módulo é a base que desbloqueia todos os demais — sem ele, estoque e fiscal não funcionam. É o gatilho de entrada natural de qualquer cliente novo.

### 2. Personas
* **Lojista / Gerente:** Cadastrar, editar e remover produtos do catálogo para manter a base atualizada.
* **Estoquista:** Consultar as especificações do produto antes de registrar movimentações físicas.
* **Contador:** Verificar e auditar a alíquota de imposto atrelada a cada produto para garantir conformidade.

### 3. Requisitos Funcionais (RF)
* **RF01 Criar produto:** Cadastrar produto exigindo SKU (alfanumérico, único), Nome, Preço Base (R$ > 0) e Alíquota de Imposto (% de 0 a 100).
* **RF02 Listar produtos:** Exibir o catálogo de produtos cadastrados com suporte a paginação.
* **RF03 Buscar produto:** Localizar um produto por correspondência exata de SKU ou parcial de Nome.
* **RF04 Editar produto:** Alterar Nome, Preço Base e Alíquota. O campo SKU é chave de negócio e **não pode ser alterado**.
* **RF05 Remover produto:** Realizar *soft delete* apenas se o módulo de Estoque confirmar que não há movimentações associadas.
* **RF06 Validar SKU único:** Rejeitar criação de produtos com SKU já existente no mesmo Tenant, retornando erro claro.

### 4. Requisitos Não-Funcionais (RNF)
* **RNF01 Segurança:** Apenas usuários autenticados podem interagir com a API. Dados obrigatoriamente isolados por empresa (`tenant_id`).
* **RNF02 Integridade:** O campo SKU deve ter restrição `UNIQUE INDEX` no banco de dados, combinada com o `tenant_id`.
* **RNF03 Performance:** Listagem e busca de até 10.000 produtos devem retornar em menos de 200ms na API.
* **RNF04 Escalabilidade:** O serviço deve suportar leituras em alta concorrência. Gravações devem garantir lock para evitar conflitos de SKU.

### 5. Especificação Técnica e Integração
**Endpoints de API:**
* `POST /v1/fisc/products` (201 Created)
* `GET /v1/fisc/products?page=1&limit=50` (200 OK)
* `GET /v1/fisc/products/{sku}` (200 OK / 404 Not Found)
* `PUT /v1/fisc/products/{sku}` (200 OK)
* `DELETE /v1/fisc/products/{sku}` (204 No Content / 409 Conflict)

**Webhooks disparados:**
* `product.created`: Payload `{ sku, nome, preco_base, aliquota_imposto }`. Consumidores: MOD2 (Estoque), MOD3 (Fiscal).
* `product.updated`: Payload `{ sku, campos_alterados }`. Consumidores: MOD2, MOD3.
* `product.deleted`: Payload `{ sku }`. Consumidores: MOD2.

**Estrutura de dados (JSON):**
```json
{
  "sku": "CAN-AZUL-001",
  "nome": "Caneta Azul BIC",
  "preco_base": 2.50,
  "aliquota_imposto": 12.00
}
```

### 6. User Stories
* "Como Lojista, eu quero cadastrar produtos de forma centralizada para garantir que estoque e fiscal usem sempre as mesmas informações."
* "Como Contador, eu quero consultar a alíquota de imposto de cada produto para validar os cálculos fiscais sem depender de planilhas."

### 7. Critérios de Aceite
* [ ] É possível criar produto com SKU, Nome, Preço Base e Alíquota.
* [ ] SKU duplicado é rejeitado com status HTTP 400 ou 409.
* [ ] É possível listar, buscar, editar e remover produtos.
* [ ] Produto com histórico no MOD2 (Estoque) não pode ser removido (retorna erro).
* [ ] Produto recém-cadastrado notifica o MOD2 para iniciar saldo zerado.

### 8. Definição de Pronto (DoD)
* [ ] Código revisado por outro membro do Squad.
* [ ] Testes unitários com >80% de cobertura.
* [ ] Documentação da API atualizada (Swagger/OpenAPI).
* [ ] Pipeline de CI/CD passando.

---

# FISC-MOD2 — Controle de Inventário (Estoque)

### 1. Visão Geral e Proposta de Valor
**Problema:** Sem controle de estoque em tempo real, vendas são confirmadas sem produto disponível ou capital fica parado em excesso de inventário sem rastreabilidade.  
**Proposta de Valor:** Registrar cada entrada e saída em tempo real (Ledger), mantendo o saldo sempre conciso e impedindo rupturas de estoque no momento da venda.

### 2. Personas
* **Estoquista:** Registrar entradas (compras/devoluções) e saídas manuais (avarias).
* **Lojista / Gerente:** Consultar saldo atual e log histórico de movimentações.
* **Sistema (Integração):** Acionar saída automática de estoque ao confirmar uma venda no MOD3.

### 3. Requisitos Funcionais (RF)
* **RF01 Registrar entrada:** Adicionar X unidades ao estoque informando SKU e quantidade.
* **RF02 Registrar saída:** Retirar X unidades do estoque informando SKU e quantidade.
* **RF03 Bloquear saída negativa:** Rejeitar saída maior que o saldo disponível com mensagem: "Estoque insuficiente. Saldo atual: X."
* **RF04 Consultar saldo:** Exibir a quantidade atual disponível de um produto pelo SKU.
* **RF05 Histórico (Ledger):** Exibir todas as movimentações imutáveis de um produto com data, hora, quantidade e tipo (IN/OUT).
* **RF06 Registrar motivo:** Exigir motivo da movimentação (ex: VENDA, COMPRA, AJUSTE, AVARIA).

### 4. Requisitos Não-Funcionais (RNF)
* **RNF01 Atomicidade:** A baixa de estoque via venda deve ocorrer em transação com a emissão da nota.
* **RNF02 Rastreabilidade:** Movimentações são imutáveis (*Append-Only*). Correções exigem registro de estorno.
* **RNF03 Performance:** Consulta de saldo em tempo real deve responder em menos de 100ms.
* **RNF04 Escalabilidade e Concorrência:** Uso de *Optimistic Locking* no banco de dados para evitar condição de corrida em vendas simultâneas do mesmo SKU.

### 5. Especificação Técnica e Integração
**Endpoints de API:**
* `POST /v1/fisc/stock/entry` (201 Created)
* `POST /v1/fisc/stock/exit` (201 Created / 422 Unprocessable Entity)
* `GET /v1/fisc/stock/{sku}/balance` (200 OK)
* `GET /v1/fisc/stock/{sku}/history` (200 OK)

**Webhooks disparados:**
* `stock.entry_registered`: Payload `{ sku, qtde, saldo_atual, motivo }`. Consumidor: MOD4 (se compra).
* `stock.exit_registered`: Payload `{ sku, qtde, saldo_atual, origem_id }`. Consumidor: MOD3.
* `stock.insufficient`: Payload `{ sku, saldo_atual, qtde_solicitada }`. Consumidor: MOD3 (bloqueia nota).

**Estrutura de dados (JSON):**
```json
{
  "sku": "CAN-AZUL-001",
  "quantidade": 50,
  "tipo": "IN",
  "motivo": "COMPRA",
  "saldo_resultante": 50
}
```

### 6. User Stories
* "Como Estoquista, eu quero registrar entradas e saídas com seus devidos motivos para manter o inventário fiel ao físico."
* "Como Lojista, eu quero consultar o histórico imutável de um produto para rastrear quebras ou sumiços."

### 7. Critérios de Aceite
* [ ] É possível registrar entrada de X unidades para um SKU válido.
* [ ] É possível registrar saída de X unidades para um SKU válido.
* [ ] Tentativa de saída maior que o saldo atual retorna erro 422 e a transação é cancelada.
* [ ] Histórico de movimentações exibe o log exato de todas as transações de um SKU.

### 8. Definição de Pronto (DoD)
* [ ] Código revisado por outro membro do Squad.
* [ ] Testes unitários com >80% de cobertura.
* [ ] Documentação da API atualizada (Swagger/OpenAPI).
* [ ] Pipeline de CI/CD passando.

---

# FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe

### 1. Visão Geral e Proposta de Valor
**Problema:** Calcular impostos manualmente por venda é lento e sujeito a erro humano, gerando riscos de autuação fiscal e multas.  
**Proposta de Valor:** Motor de regras que recebe um carrinho de produtos, cruza com as alíquotas do MOD1 e gera automaticamente um objeto estruturado (JSON) da nota fiscal.  
**Escopo:** Gera o objeto de dados fiscal calculado. A integração síncrona com SEFAZ/Prefeituras fica para versões futuras.

### 2. Personas
* **Sistema (PDV/E-commerce):** Envia a requisição com os itens vendidos para cálculo instantâneo.
* **Contador:** Acessa as intenções geradas para auditoria de tributos.

### 3. Requisitos Funcionais (RF)
* **RF01 Gerar intenção de nota:** Receber array de itens (SKU + quantidade) e retornar o JSON detalhado da tributação.
* **RF02 Calcular imposto por item:** Executar a fórmula: `imposto = preco_base × (aliquota_imposto / 100) × quantidade`.
* **RF03 Calcular totais:** Somar os valores no cabeçalho: Valor Bruto Total, Imposto Total e Valor Líquido.
* **RF04 Validar SKUs e Saldo:** Validar se o SKU existe (via MOD1) e se há saldo (via MOD2) antes de gerar a intenção.
* **RF05 Acionar eventos:** Após confirmar a intenção, disparar a ordem de baixa no estoque e lançamento financeiro.

### 4. Requisitos Não-Funcionais (RNF)
* **RNF01 Precisão Numérica:** O backend deve armazenar e calcular valores usando tipos adequados (ex: `Decimal` ou `Numeric`), não `Float`, para evitar perda de precisão em centavos.
* **RNF02 Resiliência:** Caso a requisição para o MOD1 ou MOD2 falhe durante a validação, a intenção de NFe deve ser abortada com *timeout* claro.
* **RNF03 Isolamento:** Garantir que o cálculo é aplicado usando os dados do respectivo `tenant_id`.

### 5. Especificação Técnica e Integração
**Endpoints de API:**
* `POST /v1/fisc/invoices/intent` (201 Created)
* `GET /v1/fisc/invoices/{id}` (200 OK)

**Webhooks disparados:**
* `invoice.generated`: Payload `{ invoice_id, total_bruto, total_imposto, total_liquido }`. Consumidores: MOD2 (baixa de estoque), MOD4 (entrada financeira).

**Estrutura de dados (JSON):**
```json
{
  "invoice_id": "inv_12345",
  "items": [
    {
      "sku": "CAN-AZUL-001",
      "quantidade": 2,
      "imposto_calculado": 0.60
    }
  ],
  "totais": {
    "valor_bruto": 5.00,
    "total_impostos": 0.60,
    "valor_liquido": 4.40
  }
}
```

### 6. User Stories
* "Como PDV (Sistema), eu quero enviar um carrinho de SKUs para que o motor fiscal me devolva os totais com impostos calculados em milissegundos."
* "Como Contador, eu quero que as intenções de notas tragam o detalhamento do imposto por item para evitar autuações."

### 7. Critérios de Aceite
* [ ] Requisição com SKUs válidos retorna o JSON da intenção de NFe com matemática exata.
* [ ] Requisição com um SKU inexistente retorna erro 404 detalhando qual SKU falhou.
* [ ] Geração bem sucedida dispara o webhook `invoice.generated` corretamente.

### 8. Definição de Pronto (DoD)
* [ ] Código revisado por outro membro do Squad.
* [ ] Testes unitários com >80% de cobertura (foco na lógica matemática de impostos).
* [ ] Documentação da API atualizada (Swagger/OpenAPI).
* [ ] Pipeline de CI/CD passando.

---

## Estados da Nota

### 1. Visão Geral e Proposta de Valor
**Problema:** Sem controle financeiro centralizado, o empresário confia apenas no saldo bancário, ignorando provisões de impostos e não sabendo o lucro real.  
**Proposta de Valor:** Um livro-razão automático que consolida as receitas geradas pelo módulo fiscal (MOD3) e as despesas da operação, entregando um DRE básico e saldo em tempo real.

### 2. Personas
* **Gestor Financeiro:** Acompanha saldos, extratos e insere saídas operacionais manuais.
* **Sistema (Integração):** Subscreve-se nas notas emitidas para popular a receita automaticamente.

### 3. Requisitos Funcionais (RF)
* **RF01 Entrada automática:** Toda nota confirmada (via webhook `invoice.generated`) gera uma transação de CRÉDITO automaticamente.
* **RF02 Registrar despesa:** Permitir cadastro de DÉBITO manual informando descrição, valor (> 0) e data.
* **RF03 Consultar saldo atual:** Calcular e exibir o saldo consolidado do Tenant (Entradas − Saídas).
* **RF04 Extrato por período:** Listar as transações filtradas através de datas (Data Início e Data Fim).
* **RF05 Resumo consolidado:** Ao puxar o extrato, devolver no cabeçalho a somatória: Total de Entradas e Total de Saídas do período solicitado.

### 4. Requisitos Não-Funcionais (RNF)
* **RNF01 Imutabilidade Financeira:** Transações inseridas no fluxo não podem ser excluídas (*Hard Delete* proibido). Para corrigir, é obrigatório lançar um estorno inverso.
* **RNF02 Consistência:** A leitura do saldo atualizado deve ser instantânea, processando o fluxo de caixa de maneira performática.

### 5. Especificação Técnica e Integração
**Endpoints de API:**
* `POST /v1/fisc/cashflow/expense` (201 Created)
* `GET /v1/fisc/cashflow/balance` (200 OK)
* `GET /v1/fisc/cashflow/statement?start={data}&end={data}` (200 OK)

**Consumo de Webhooks:**
* Ouve o `invoice.generated` emitido pelo MOD3 para gerar transação com tipo `CREDITO`.

**Estrutura de dados (JSON):**
```json
{
  "transaction_id": "tx_9988",
  "tipo": "CREDITO",
  "valor": 5.00,
  "descricao": "Venda ref. invoice inv_12345",
  "data_ocorrencia": "2026-03-09T10:00:00Z"
}
```

### 6. User Stories
* "Como Gestor Financeiro, eu quero que as notas fiscais emitidas gerem receitas automaticamente no caixa para não ter que fazer duplo lançamento."
* "Como Gestor Financeiro, eu quero tirar um extrato por intervalo de datas para avaliar a saúde da empresa."

### 7. Critérios de Aceite
* [ ] Evento de nota emitida gera entrada de CRÉDITO com os valores corretos.
* [ ] API permite registrar despesa manual de DÉBITO.
* [ ] Consulta de extrato com filtro de data retorna apenas os lançamentos do período estipulado.
* [ ] Endpoint de saldo soma todas as entradas e subtrai as saídas com sucesso.

### 8. Definição de Pronto (DoD)
* [ ] Código revisado por outro membro do Squad.
* [ ] Integração E2E (MOD3 dispara, MOD4 escuta) validada.
* [ ] Testes unitários com >80% de cobertura.
* [ ] Documentação da API atualizada (Swagger/OpenAPI).
* [ ] Pipeline de CI/CD passando.
```
