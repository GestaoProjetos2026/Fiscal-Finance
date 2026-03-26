# 📄 PRD — Squad FISC: Fiscal, Financeiro & Estoque

Emissão de NFe/NFSe · Fluxo de Caixa · Controle de Inventário

**Versão:** 1.1 · **Sprint:** 1 · **Status:** Em revisão · **Data:** 25/03/2026

---

## Índice de Módulos

1. FISC-MOD1 — Cadastro de Produtos
2. FISC-MOD2 — Controle de Inventário (Estoque)
3. FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe
4. FISC-MOD4 — Fluxo de Caixa

---

# FISC-MOD1 — Cadastro de Produtos

## 1. Visão Geral e Proposta de Valor

Problema: Sem cadastro centralizado, o estoque não conhece o preço do produto e o setor fiscal não sabe qual alíquota aplicar — cada área trabalha com sua própria planilha, gerando inconsistências.

Proposta de Valor: Centralizar as informações de cada produto (código, nome, preço e imposto) em um único registro que alimenta automaticamente o estoque e o cálculo fiscal.

Oportunidade de Venda: Qualquer negócio que vende produtos físicos precisa de um catálogo centralizado antes de qualquer outra coisa. Este módulo é a base que desbloqueia todos os demais — sem ele, estoque e fiscal não funcionam. É o ponto de entrada natural de qualquer cliente novo.

---

## 2. Personas

* Lojista / Gerente: Cadastrar, editar e remover produtos do catálogo.
* Estoquista: Consultar produtos antes de registrar movimentações.
* Contador: Verificar a alíquota de imposto de cada produto.

---

## 3. Requisitos Funcionais (RF)

* RF01 Criar produto: Cadastrar produto com SKU (único), Nome, Preço Base (R$) e Alíquota de Imposto (%).
* RF02 Listar produtos: Exibir todos os produtos cadastrados.
* RF03 Buscar produto: Localizar produto pelo SKU ou pelo Nome.
* RF04 Editar produto: Alterar Nome, Preço Base e Alíquota. O SKU não pode ser alterado.
* RF05 **Inativar produto:** Em vez de remover fisicamente, o produto deve ser marcado como inativo, preservando o histórico de movimentações.
* RF06 Validar SKU único: Rejeitar cadastro de produto com SKU já existente, com mensagem de erro.

---

## 4. Requisitos Não-Funcionais (RNF)

* RNF01 Segurança: Apenas usuários autenticados podem criar, editar ou remover produtos. Dados isolados por empresa (tenant).
* RNF02 Integridade: O SKU deve ser único em todo o sistema — sem duplicação possível.
* RNF03 Performance: Listagem de até 10.000 produtos deve retornar em menos de 1 segundo.
* RNF04 Escalabilidade: O serviço deve suportar leituras em alta concorrência via cache (Redis/similar). Gravações via fila para evitar conflitos de SKU em múltiplas instâncias.

---

## 5. Especificação Técnica e Integração

Endpoints de API (referência para Sprint 2)

```
POST /v1/fisc/products -> 201 Created
GET /v1/fisc/products -> 200 OK
GET /v1/fisc/products/{sku} -> 200 OK / 404 Not Found
PUT /v1/fisc/products/{sku} -> 200 OK
PATCH /v1/fisc/products/{sku}/status -> 200 OK
DELETE /v1/fisc/products/{sku} -> 204 No Content (opcional, apenas se permitido)
```

**Códigos de erro:**

* 409 Conflict → SKU duplicado
* 422 Unprocessable Entity → dados inválidos

---

**Webhooks disparados por este módulo**

* product.created → `{ sku, nome, preco_base, aliquota_imposto }`
* product.updated → `{ sku, campos_alterados }`
* product.deleted → `{ sku }`

---

**Estrutura de dados — Produto**

```json
{
  "sku": "CAN-AZUL-001",
  "nome": "Caneta Azul BIC",
  "preco_base": 2.50,
  "aliquota_imposto": 0.12,
  "ativo": true
}
```

---

## 6. User Stories

"Como Lojista, eu quero cadastrar produtos para organizar meu catálogo e garantir que estoque e fiscal usem sempre as mesmas informações."

"Como Contador, eu quero consultar a alíquota de imposto de cada produto para validar os cálculos fiscais sem depender de planilhas paralelas."

---

## 7. Critérios de Aceite

* É possível criar produto com SKU, Nome, Preço Base e Alíquota.
* SKU duplicado é rejeitado com mensagem de erro.
* É possível listar, editar e inativar produtos.
* Produto com movimentações não deve ser removido fisicamente.
* Produto recém-cadastrado inicia com saldo de estoque = 0.

---

## 8. Definição de Pronto (DoD)

* Código revisado por outro membro do Squad.
* Testes unitários com >80% de cobertura.
* Documentação da API atualizada (Swagger/OpenAPI).
* Pipeline de CI/CD passando.
* Webhooks validados por MOD2 e MOD3.

---

# FISC-MOD2 — Controle de Inventário (Estoque)

## 1. Visão Geral e Proposta de Valor

Problema: Sem controle de estoque em tempo real, vendas são confirmadas sem produto disponível ou produtos ficam parados por excesso sem que ninguém perceba.

Proposta de Valor: Registrar cada entrada e saída de produto em tempo real, mantendo o saldo correto e impedindo vendas de itens indisponíveis.

---

## 2. Personas

* Estoquista: Registrar entradas e saídas
* Lojista / Gerente: Consultar saldo e histórico
* Sistema Fiscal: Acionar saída de estoque

---

## 3. Requisitos Funcionais (RF)

* RF01 Registrar entrada
* RF02 Registrar saída
* RF03 Bloquear saída negativa
* RF04 Consultar saldo
* RF05 Histórico de movimentações
* RF06 Registrar motivo

---

## 4. Requisitos Não-Funcionais (RNF)

* Atomicidade garantida
* Rastreabilidade completa
* Performance otimizada
* Controle de concorrência

---

## 5. Especificação Técnica e Integração

```
POST /v1/fisc/stock/entry
POST /v1/fisc/stock/exit
GET /v1/fisc/stock/{sku}
GET /v1/fisc/stock/{sku}/history?from=YYYY-MM-DD&to=YYYY-MM-DD
```

✔ Histórico agora suporta filtro por data

---

## 6. User Stories

(inalterado)

---

## 7. Critérios de Aceite

* Entrada e saída funcionam corretamente
* Estoque nunca fica negativo
* Histórico atualizado corretamente
* Filtro por data retorna resultados corretos

---

# FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe

## 1. Visão Geral e Proposta de Valor

(inalterado)

---

## 2. Requisitos Funcionais (RF)

* RF01 Gerar intenção de nota
* RF02 Calcular imposto
* RF03 Calcular totais
* RF04 Validar SKUs
* RF05 Acionar baixa de estoque

---

## Controle de Consistência entre Módulos

Fluxo obrigatório:

1. Nota criada como `PENDING`
2. Validação de estoque (MOD2)
3. Registro financeiro (MOD4)
4. Nota confirmada (`CONFIRMED`)

Falha:

* status `FAILED`
* nenhuma operação parcial

---

## Estados da Nota

* PENDING
* CONFIRMED
* FAILED

---

## 3. Especificação Técnica e Integração

```
POST /v1/fisc/invoice/intent
GET /v1/fisc/invoice/{id}
```

---

# FISC-MOD4 — Fluxo de Caixa

## 1. Visão Geral e Proposta de Valor

(inalterado)

---

## 2. Requisitos Funcionais (RF)

* RF01 Entrada automática
* RF02 Registrar despesa
* RF03 Consultar saldo
* RF04 Extrato por período
* RF05 Resumo financeiro

---

## 3. Especificação Técnica e Integração

```
POST /v1/fisc/cashflow/entry
POST /v1/fisc/cashflow/expense
GET /v1/fisc/cashflow/balance
GET /v1/fisc/cashflow/statement?from=&to=
```

---

## 4. Definição de Pronto (DoD) Geral

* Código revisado
* Testes >80%
* Documentação atualizada
* CI/CD ok
* Integração validada

---
