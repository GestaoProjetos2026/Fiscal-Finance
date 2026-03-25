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

Problema: Sem cadastro centralizado, o estoque não conhece o preço do produto e o setor fiscal não sabe qual alíquota aplicar — cada área trabalha com sua própria planilha, gerando inconsistências.

Proposta de Valor: Centralizar as informações de cada produto (código, nome, preço e imposto) em um único registro que alimenta automaticamente o estoque e o cálculo fiscal.

Oportunidade de Venda: Qualquer negócio que vende produtos físicos precisa de um catálogo centralizado antes de qualquer outra coisa. Este módulo é a base que desbloqueia todos os demais — sem ele, estoque e fiscal não funcionam. É o ponto de entrada natural de qualquer cliente novo.

---

### 2. Personas

- Lojista / Gerente: Cadastrar, editar e remover produtos do catálogo.
- Estoquista: Consultar produtos antes de registrar movimentações.
- Contador: Verificar a alíquota de imposto de cada produto.

---

### 3. Requisitos Funcionais (RF)

- RF01 Criar produto: Cadastrar produto com SKU (único), Nome, Preço Base (R$) e Alíquota de Imposto (%).
- RF02 Listar produtos: Exibir todos os produtos cadastrados.
- RF03 Buscar produto: Localizar produto pelo SKU ou pelo Nome.
- RF04 Editar produto: Alterar Nome, Preço Base e Alíquota. O SKU não pode ser alterado.
- RF05 Remover produto: Remover produto apenas se não houver movimentações de estoque associadas.
- RF06 Validar SKU único: Rejeitar cadastro de produto com SKU já existente, com mensagem de erro.

---

### 4. Requisitos Não-Funcionais (RNF)

- RNF01 Segurança: Apenas usuários autenticados podem criar, editar ou remover produtos. Dados isolados por empresa (tenant).
- RNF02 Integridade: O SKU deve ser único em todo o sistema — sem duplicação possível.
- RNF03 Performance: Listagem completa deve retornar em tempo aceitável para o usuário (< 3 segundos no ambiente local). Em produção, o objetivo é < 1 segundo via indexação do banco.
- RNF04 Escalabilidade: Conflitos de SKU são prevenidos via `UNIQUE constraint` no banco de dados. Para o ambiente local de desenvolvimento, isso é suficiente. Escalabilidade horizontal (Redis/filas) é escopo de versões futuras.


---

### 5. Especificação Técnica e Integração

Endpoints de API (referência para Sprint 2)

POST /v1/fisc/products -> Cria produto
GET /v1/fisc/products -> Lista produtos
GET /v1/fisc/products/{sku} -> Busca por SKU
PUT /v1/fisc/products/{sku} -> Atualiza produto
DELETE /v1/fisc/products/{sku} -> Remove produto

Webhooks disparados por este módulo
- product.created: Payload { sku, nome, preco_base, aliquota_imposto }. Consumidores: MOD2 (Estoque), MOD3 (Fiscal).
- product.updated: Payload { sku, campos_alterados }. Consumidores: MOD2, MOD3.
- product.deleted: Payload { sku }. Consumidores: MOD2 (para invalidar cache de saldo).

Estrutura de dados — Produto
{
"sku": "CAN-AZUL-001",
"nome": "Caneta Azul BIC",
"preco_base": 2.50,
"aliquota_imposto": 0.12
}

---

### 6. User Stories

"Como Lojista, eu quero cadastrar produtos para organizar meu catálogo e garantir que estoque e fiscal usem sempre as mesmas informações."

"Como Contador, eu quero consultar a alíquota de imposto de cada produto para validar os cálculos fiscais sem depender de planilhas paralelas."

"Como Estoquista, eu quero buscar um produto pelo nome para confirmar que ele existe no catálogo antes de registrar uma entrada no estoque."

---

### 7. Critérios de Aceite

- É possível criar produto com SKU, Nome, Preço Base e Alíquota.
- SKU duplicado é rejeitado com mensagem de erro.
- É possível listar, editar e remover produtos.
- Produto com movimentações de estoque não pode ser removido.
- Produto recém-cadastrado inicia com saldo de estoque = 0.

---

### 8. Definição de Pronto (DoD)

- [ ] Código revisado por outro membro do Squad.
- [ ] Funções críticas (criar, validar SKU, remover) com ao menos 1 teste unitário funcional.

---

## FISC-MOD2 — Controle de Inventário (Estoque)

### 1. Visão Geral e Proposta de Valor

Problema: Sem controle de estoque em tempo real, vendas são confirmadas sem produto disponível ou produtos ficam parados por excesso sem que ninguém perceba.

Proposta de Valor: Registrar cada entrada e saída de produto em tempo real, mantendo o saldo correto e impedindo vendas de itens indisponíveis.

Oportunidade de Venda: Controle de estoque é um dos serviços mais procurados por pequenos comerciantes. Pode ser vendido separadamente do módulo fiscal como uma solução de gestão de inventário, sem exigir os outros módulos.

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

- RNF01 Atomicidade: Saída de estoque ocorre dentro de uma transação de banco de dados. Se qualquer etapa falhar, a transação é revertida (ROLLBACK). Isso é suficiente para o ambiente local e implementável em PHP com PDO Transactions.
- RNF02 Rastreabilidade: Movimentações são imutáveis após registro — correções via estorno.
- RNF03 Performance: Consulta de saldo deve responder em menos de 300ms.
- RNF04 Escalabilidade: Conflitos de concorrência são tratados via `SELECT FOR UPDATE` (lock pessimista) no banco de dados durante operações de saída. Suficiente para o volume de uso esperado.

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

Como Sistema Fiscal (MOD3), eu quero registrar automaticamente a saída do estoque ao confirmar uma nota para que o inventário sempre reflita as vendas realizadas.

---

### 7. Critérios de Aceite

- É possível registrar ENTRADA de X unidades por SKU.
- É possível registrar SAÍDA de X unidades por SKU.
- Saída maior que o saldo é bloqueada com mensagem de erro.
- Saldo é atualizado imediatamente após cada movimentação.
  
### 8. Definição de Pronto (DoD)
- [ ] Código revisado via Pull Request.
- [ ] Testes nas funções de entrada, saída e bloqueio de saldo insuficiente.
- [ ] Endpoints documentados em README_API.md.
- [ ] Testado via Postman/Insomnia.

---

## FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe

### 1. Visão Geral e Proposta de Valor

Problema: Calcular impostos manualmente por venda é lento e sujeito a erro, gerando riscos de autuação fiscal.

Proposta de Valor: Dado um conjunto de produtos/serviços vendidos, o módulo calcula automaticamente os impostos e gera um objeto estruturado (JSON) representando a "intenção de nota fiscal".

Oportunidade de Venda: A calculadora fiscal pode ser vendida como um componente de API para sistemas já existentes que precisam pré-calcular impostos antes de emitir nota. Serve como "trial" do módulo de emissão completo.

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
> POST /v1/fisc/invoice/intent    -> Calcula impostos e retorna rascunho (sem salvar)
> POST /v1/fisc/invoice/confirm   -> Confirma nota, baixa estoque e lança financeiro
> GET  /v1/fisc/invoice/{id}      -> Consulta nota confirmada por ID

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
