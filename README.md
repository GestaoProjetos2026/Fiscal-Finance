# PRD — Squad FISC: Fiscal, Financeiro & Estoque\
> Emissão de NFe/NFSe · Fluxo de Caixa · Controle de Inventário\
\
**Versão:** 1.0 · **Sprint:** 1 · **Status:** Em revisão · **Data:** 09/03/2026\
\
---\
\
## Índice de Módulos\
1. [FISC-MOD1 — Cadastro de Produtos](#fisc-mod1--cadastro-de-produtos)\
2. [FISC-MOD2 — Controle de Inventário (Estoque)](#fisc-mod2--controle-de-inventário-estoque)\
3. [FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe](#fisc-mod3--calculadora-fiscal--intenção-de-nfe-e-nfse)\
4. [FISC-MOD4 — Fluxo de Caixa](#fisc-mod4--fluxo-de-caixa)\
\
---\
\
## FISC-MOD1 — Cadastro de Produtos\
\
### 1. Visão Geral e Proposta de Valor\
\
**Problema:** Sem cadastro centralizado, o estoque não conhece o preço do produto e o setor fiscal não sabe qual alíquota aplicar — cada área trabalha com sua própria planilha, gerando inconsistências.\
\
**Proposta de Valor:** Centralizar as informações de cada produto (código, nome, preço e imposto) em um único registro que alimenta automaticamente o estoque e o cálculo fiscal.\
\
**Oportunidade de Venda:** Qualquer negócio que vende produtos físicos precisa de um catálogo centralizado antes de qualquer outra coisa. Este módulo é a base que desbloqueia todos os demais — sem ele, estoque e fiscal não funcionam. É o ponto de entrada natural de qualquer cliente novo.\
\
---\
\
### 2. Personas\
\
| Persona | O que precisa neste módulo |\
|---|---|\
| Lojista / Gerente | Cadastrar, editar e remover produtos do catálogo |\
| Estoquista | Consultar produtos antes de registrar movimentações |\
| Contador | Verificar a alíquota de imposto de cada produto |\
\
---\
\
### 3. Requisitos Funcionais (RF)\
\
| ID | Nome | Descrição |\
|---|---|---|\
| RF01 | Criar produto | Cadastrar produto com: SKU (único), Nome, Preço Base (R$) e Alíquota de Imposto (%). |\
| RF02 | Listar produtos | Exibir todos os produtos cadastrados. |\
| RF03 | Buscar produto | Localizar produto pelo SKU ou pelo Nome. |\
| RF04 | Editar produto | Alterar Nome, Preço Base e Alíquota. O SKU não pode ser alterado. |\
| RF05 | Remover produto | Remover produto apenas se não houver movimentações de estoque associadas. |\
| RF06 | Validar SKU único | Rejeitar cadastro de produto com SKU já existente, com mensagem de erro. |\
\
---\
\
### 4. Requisitos Não-Funcionais (RNF)\
\
| ID | Categoria | Descrição |\
|---|---|---|\
| RNF01 | Segurança | Apenas usuários autenticados podem criar, editar ou remover produtos. Dados isolados por empresa (tenant). |\
| RNF02 | Integridade | O SKU deve ser único em todo o sistema — sem duplicação possível. |\
| RNF03 | Performance | Listagem de até 10.000 produtos deve retornar em menos de 1 segundo. |\
| RNF04 | Escalabilidade | O serviço deve suportar leituras em alta concorrência via cache (Redis/similar). Gravações via fila para evitar conflitos de SKU em múltiplas instâncias. |\
\
---\
\
### 5. Especificação Técnica e Integração\
\
**Endpoints de API** _(referência para Sprint 2)_\
```\
POST /v1/fisc/products → Cria produto\
GET /v1/fisc/products → Lista produtos\
GET /v1/fisc/products/{sku} → Busca por SKU\
PUT /v1/fisc/products/{sku} → Atualiza produto\
DELETE /v1/fisc/products/{sku} → Remove produto\
```\
\
**Webhooks disparados por este módulo**\
| Evento | Payload | Consumidores |\
|---|---|---|\
| `product.created` | `{ sku, nome, preco_base, aliquota_imposto }` | MOD2 (Estoque), MOD3 (Fiscal) |\
| `product.updated` | `{ sku, campos_alterados }` | MOD2, MOD3 |\
| `product.deleted` | `{ sku }` | MOD2 (para invalidar cache de saldo) |\
\
**Diagrama de Dados — Entidade Produto**\
```mermaid\
erDiagram\
PRODUTO {\
string sku PK\
string nome\
float preco_base\
float aliquota_imposto\
datetime criado_em\
datetime atualizado_em\
}\
PRODUTO ||--o{ MOVIMENTACAO_ESTOQUE : "possui"\
PRODUTO ||--o{ ITEM_NOTA_FISCAL : "compõe"\
```\
\
**Estrutura de dados — Produto**\
```json\
{\
"sku": "CAN-AZUL-001",\
"nome": "Caneta Azul BIC",\
"preco_base": 2.50,\
"aliquota_imposto": 0.12\
}\
```\
\
---\
\
### 6. User Stories\
\
> *"Como Lojista, eu quero cadastrar produtos para organizar meu catálogo e garantir que estoque e fiscal usem sempre as mesmas informações."*\
\
> *"Como Contador, eu quero consultar a alíquota de imposto de cada produto para validar os cálculos fiscais sem depender de planilhas paralelas."*\
\
---\
\
### 7. Critérios de Aceite\
\
- [ ] É possível criar produto com SKU, Nome, Preço Base e Alíquota\
- [ ] SKU duplicado é rejeitado com mensagem de erro\
- [ ] É possível listar, editar e remover produtos\
- [ ] Produto com movimentações de estoque não pode ser removido\
- [ ] Produto recém-cadastrado inicia com saldo de estoque = 0\
\
---\
\
### 8. Definição de Pronto (DoD)\
\
- [ ] Código revisado por outro membro do Squad\
- [ ] Testes unitários com >80% de cobertura\
- [ ] Documentação da API atualizada (Swagger/OpenAPI)\
- [ ] Pipeline de CI/CD passando\
- [ ] Webhooks validados por MOD2 e MOD3\
\
---\
\
## FISC-MOD2 — Controle de Inventário (Estoque)\
\
### 1. Visão Geral e Proposta de Valor\
\
**Problema:** Sem controle de estoque em tempo real, vendas são confirmadas sem produto disponível ou produtos ficam parados por excesso sem que ninguém perceba.\
\
**Proposta de Valor:** Registrar cada entrada e saída de produto em tempo real, mantendo o saldo correto e impedindo vendas de itens indisponíveis.\
\
**Oportunidade de Venda:** Negócios com estoque físico perdem dinheiro todo dia por falta ou excesso de produto. Este módulo entrega controle em tempo real com rastreabilidade total — algo que planilhas simplesmente não conseguem fazer de forma confiável.\
\
---\
\
### 2. Personas\
\
| Persona | O que precisa neste módulo |\
|---|---|\
| Estoquista | Registrar entradas (compras/devoluções) e saídas (vendas) |\
| Lojista / Gerente | Consultar saldo atual e histórico de movimentações |\
| Sistema Fiscal (interno) | Acionar saída de estoque ao confirmar uma venda |\
\
---\
\
### 3. Requisitos Funcionais (RF)\
\
| ID | Nome | Descrição |\
|---|---|---|\
| RF01 | Registrar entrada | Adicionar X unidades ao estoque de um produto, informando SKU e quantidade. |\
| RF02 | Registrar saída | Retirar X unidades do estoque informando SKU e quantidade. |\
| RF03 | Bloquear saída negativa | Rejeitar saída maior que o saldo disponível com mensagem: "Estoque insuficiente. Saldo atual: X." |\
| RF04 | Consultar saldo | Exibir a quantidade disponível de um produto pelo SKU. |\
| RF05 | Histórico | Exibir todas as movimentações de um produto com data, hora, quantidade e tipo. |\
| RF06 | Registrar motivo | Permitir informar motivo da movimentação (ex: venda, devolução, ajuste). |\
\
---\
\
### 4. Requisitos Não-Funcionais (RNF)\
\
| ID | Categoria | Descrição |\
|---|---|---|\
| RNF01 | Atomicidade | Saída de estoque e confirmação de venda ocorrem juntas. Se a venda falhar, o estoque não é alterado. |\
| RNF02 | Rastreabilidade | Movimentações são imutáveis após registro — correções via estorno. |\
| RNF03 | Performance | Consulta de saldo deve responder em menos de 300ms. |\
| RNF04 | Escalabilidade | Operações de entrada/saída usam lock otimista por SKU para evitar condição de corrida em ambientes com múltiplos usuários simultâneos. |\
\
---\
\
### 5. Especificação Técnica e Integração\
\
**Endpoints de API**\
```\
POST /v1/fisc/stock/entry → Registra entrada\
POST /v1/fisc/stock/exit → Registra saída\
GET /v1/fisc/stock/{sku} → Consulta saldo\
GET /v1/fisc/stock/{sku}/history → Histórico do produto\
```\
\
**Webhooks disparados por este módulo**\
| Evento | Payload | Consumidores |\
|---|---|---|\
| `stock.entry_registered` | `{ sku, quantidade, saldo_atual, motivo }` | MOD4 (Fluxo de Caixa, se compra) |\
| `stock.exit_registered` | `{ sku, quantidade, saldo_atual, nota_id }` | MOD3 (confirmação de baixa) |\
| `stock.insufficient` | `{ sku, saldo_atual, quantidade_solicitada }` | MOD3 (para bloquear nota) |\
\
**Diagrama de Dados — Movimentação de Estoque**\
```mermaid\
erDiagram\
PRODUTO ||--o{ MOVIMENTACAO_ESTOQUE : "possui"\
MOVIMENTACAO_ESTOQUE {\
int id PK\
string sku FK\
string tipo\
int quantidade\
string motivo\
int nota_id FK\
datetime registrado_em\
}\
```\
\
**Exemplo — payload de entrada de estoque**\
```json\
{ "sku": "CAN-AZUL-001", "quantidade": 100, "motivo": "compra do fornecedor" }\
```\
\
**Exemplo — retorno de saldo**\
```json\
{ "sku": "CAN-AZUL-001", "nome": "Caneta Azul BIC", "saldo_atual": 90 }\
```\
\
---\
\
### 6. User Stories\
\
> *"Como Estoquista, eu quero registrar entradas e saídas de produtos para manter o inventário atualizado em tempo real."*\
\
> *"Como Lojista, eu quero consultar o histórico de movimentações de um produto para entender o que aconteceu com o meu estoque."*\
\
---\
\
### 7. Critérios de Aceite\
\
- [ ] É possível registrar ENTRADA de X unidades por SKU\
- [ ] É possível registrar SAÍDA de X unidades por SKU\
- [ ] Saída maior que o saldo é bloqueada com mensagem de erro\
- [ ] Data e hora são registradas automaticamente\
- [ ] Saldo é atualizado imediatamente após cada movimentação\
- [ ] É possível consultar saldo atual e histórico de qualquer produto\
\
---\
\
### 8. Definição de Pronto (DoD)\
\
- [ ] Código revisado por outro membro do Squad\
- [ ] Testes unitários com >80% de cobertura (incluindo cenário de saldo insuficiente)\
- [ ] Documentação da API atualizada (Swagger/OpenAPI)\
- [ ] Pipeline de CI/CD passando\
- [ ] Atomicidade validada com teste de concorrência\
\
---\
\
## FISC-MOD3 — Calculadora Fiscal / Intenção de NFe e NFSe\
\
### 1. Visão Geral e Proposta de Valor\
\
**Problema:** Calcular impostos manualmente por venda é lento e sujeito a erro, gerando riscos de autuação fiscal.\
\
**Proposta de Valor:** Dado um conjunto de produtos/serviços vendidos, o módulo calcula automaticamente os impostos e gera um objeto estruturado (JSON) representando a "intenção de nota fiscal" — seja NFe (mercadorias) ou NFSe (serviços).\
\
> **ℹ Escopo:** O módulo gera o objeto de dados fiscal calculado. A emissão real junto à SEFAZ / Prefeitura (com certificado digital) é escopo de versões futuras.\
\
**Oportunidade de Venda:** Erros fiscais geram multas e autuações — dores que qualquer empresário quer evitar. Este módulo elimina o risco de cálculo manual e cria um registro rastreável de cada nota, o que é especialmente valioso para empresas em crescimento que precisam de conformidade fiscal.\
\
---\
\
### 2. Personas\
\
| Persona | O que precisa neste módulo |\
|---|---|\
| Contador | Confirmar que o cálculo de impostos está correto por venda/serviço |\
| Sistema de Vendas (futuro) | Receber o JSON com os valores calculados |\
| Lojista / Gerente | Ver o total de imposto recolhido em um período |\
\
---\
\
### 3. Requisitos Funcionais (RF)\
\
| ID | Nome | Descrição |\
|---|---|---|\
| RF01 | Gerar intenção de nota | Recebe lista de itens (SKU + quantidade) e retorna o JSON completo da nota com todos os valores calculados. |\
| RF02 | Calcular imposto por item | Fórmula: `imposto = preco_base × aliquota_imposto × quantidade` |\
| RF03 | Calcular totais | Soma valor bruto total, imposto total e valor final total da nota. |\
| RF04 | Validar SKUs | Retorna erro identificando qualquer SKU não encontrado no cadastro. |\
| RF05 | Acionar baixa de estoque | Ao confirmar a nota, solicita saída de estoque para todos os itens (atomicidade com MOD2). |\
\
---\
\
### 4. Requisitos Não-Funcionais (RNF)\
\
| ID | Categoria | Descrição |\
|---|---|---|\
| RNF01 | Atomicidade | Se o cálculo falhar ou estoque for insuficiente, a nota não é gerada e o estoque não baixa. |\
| RNF02 | Modelo fiscal | Utiliza alíquota genérica por produto — sem distinção ICMS/ISS nesta versão. |\
| RNF03 | Formato padronizado | Retorno sempre em JSON estruturado e validado. |\
| RNF04 | Escalabilidade | Geração de notas é stateless e pode ser paralelizada horizontalmente. Cada requisição é independente. |\
\
---\
\
### 5. Especificação Técnica e Integração\
\
**Endpoints de API**\
```\
POST /v1/fisc/invoice/intent → Gera intenção de nota fiscal (NFe ou NFSe)\
GET /v1/fisc/invoice/{id} → Consulta nota por ID\
```\
\
**Webhooks disparados por este módulo**\
| Evento | Payload | Consumidores |\
|---|---|---|\
| `invoice.generated` | `{ id, total_bruto, total_imposto, total_final, data_emissao }` | MOD2 (baixa de estoque), MOD4 (entrada financeira) |\
| `invoice.failed` | `{ motivo, itens_invalidos }` | Caller (para notificar o usuário) |\
\
**Diagrama de Dados — Nota Fiscal**\
```mermaid\
erDiagram\
NOTA_FISCAL {\
int id PK\
datetime data_emissao\
float total_bruto\
float total_imposto\
float total_final\
string status\
}\
ITEM_NOTA_FISCAL {\
int id PK\
int nota_id FK\
string sku FK\
int quantidade\
float preco_unitario\
float aliquota\
float subtotal_bruto\
float subtotal_imposto\
float subtotal_final\
}\
NOTA_FISCAL ||--|{ ITEM_NOTA_FISCAL : "contém"\
ITEM_NOTA_FISCAL }o--|| PRODUTO : "referencia"\
```\
\
**Payload de entrada**\
```json\
{\
"itens": [\
{ "sku": "CAN-AZUL-001", "quantidade": 10 },\
{ "sku": "CAD-A4-002", "quantidade": 5 }\
]\
}\
```\
\
**Retorno gerado**\
```json\
{\
"id": 1,\
"data_emissao": "2026-03-09T18:00:00",\
"itens": [\
{\
"sku": "CAN-AZUL-001", "nome": "Caneta Azul BIC",\
"quantidade": 10, "preco_unitario": 2.50, "aliquota": 0.12,\
"subtotal_bruto": 25.00, "subtotal_imposto": 3.00, "subtotal_final": 28.00\
},\
{\
"sku": "CAD-A4-002", "nome": "Caderno A4",\
"quantidade": 5, "preco_unitario": 15.00, "aliquota": 0.10,\
"subtotal_bruto": 75.00, "subtotal_imposto": 7.50, "subtotal_final": 82.50\
}\
],\
"total_bruto": 100.00,\
"total_imposto": 10.50,\
"total_final": 110.50\
}\
```\
\
---\
\
### 6. User Stories\
\
> *"Como Contador, eu quero o cálculo automático de impostos para evitar erros fiscais e garantir conformidade."*\
\
> *"Como Lojista, eu quero gerar a intenção de nota com um clique para agilizar o fechamento de cada venda."*\
\
---\
\
### 7. Critérios de Aceite\
\
- [ ] Dado uma lista de itens, o sistema calcula valor bruto, imposto e total por item e para a nota\
- [ ] SKU inválido retorna erro identificando qual código é o problema\
- [ ] Estoque insuficiente bloqueia a geração da nota com mensagem de erro\
- [ ] A baixa de estoque só ocorre se a nota for gerada com sucesso\
- [ ] Retorno é um JSON válido e estruturado\
\
---\
\
### 8. Definição de Pronto (DoD)\
\
- [ ] Código revisado por outro membro do Squad\
- [ ] Testes unitários com >80% de cobertura (incluindo cálculos fiscais e cenários de falha)\
- [ ] Documentação da API atualizada (Swagger/OpenAPI)\
- [ ] Pipeline de CI/CD passando\
- [ ] Integração com MOD2 (baixa de estoque) e MOD4 (entrada financeira) validada end-to-end\
\
---\
\
## FISC-MOD4 — Fluxo de Caixa\
\
### 1. Visão Geral e Proposta de Valor\
\
**Problema:** Sem controle financeiro centralizado, o empresário não sabe se a empresa está lucrando. As vendas acontecem mas não existe visão consolidada do dinheiro que entra e sai.\
\
**Proposta de Valor:** Registrar automaticamente cada transação financeira vinculada à nota fiscal gerada e permitir visualizar saldo e extrato do período.\
\
> **ℹ Integração:** Toda nota fiscal confirmada no MOD3 gera automaticamente uma entrada financeira neste módulo.\
\
**Oportunidade de Venda:** "Faturei muito, mas cadê o dinheiro?" é a pergunta mais comum de pequenos empresários. Este módulo responde essa pergunta em tempo real, com rastreabilidade total ligada a cada nota — algo que nenhuma planilha manual consegue entregar com segurança.\
\
---\
\
### 2. Personas\
\
| Persona | O que precisa neste módulo |\
|---|---|\
| Lojista / Gerente | Ver saldo financeiro atual e extrato do período |\
| Contador | Conciliar valores de vendas com impostos recolhidos |\
\
---\
\
### 3. Requisitos Funcionais (RF)\
\
| ID | Nome | Descrição |\
|---|---|---|\
| RF01 | Entrada automática | Toda nota confirmada gera entrada com: valor bruto, imposto, valor líquido e data/hora. |\
| RF02 | Registrar despesa | Registrar saída financeira manual com: descrição, valor e data. |\
| RF03 | Consultar saldo | Calcular e exibir saldo atual: entradas − saídas. |\
| RF04 | Extrato por período | Listar todas as transações dentro de um intervalo de datas. |\
| RF05 | Resumo financeiro | Exibir: total de entradas, total de saídas, total de impostos e saldo líquido do período. |\
\
---\
\
### 4. Requisitos Não-Funcionais (RNF)\
\
| ID | Categoria | Descrição |\
|---|---|---|\
| RNF01 | Rastreabilidade | Transações são imutáveis — correções via estorno, nunca por edição. |\
| RNF02 | Vínculo | Cada entrada financeira referencia o ID da nota fiscal que a originou. |\
| RNF03 | Isolamento | Dados financeiros de cada empresa são completamente separados (multi-tenant). |\
| RNF04 | Escalabilidade | Extrato e saldo são calculados via queries otimizadas com índices por data e empresa. Suporta histórico de anos sem degradação perceptível. |\
\
---\
\
### 5. Especificação Técnica e Integração\
\
**Endpoints de API**\
```\
POST /v1/fisc/cashflow/entry → Registra entrada financeira\
POST /v1/fisc/cashflow/expense → Registra despesa/saída\
GET /v1/fisc/cashflow/balance → Consulta saldo atual\
GET /v1/fisc/cashflow/statement → Extrato (?from=&to=)\
```\
\
**Webhooks disparados por este módulo**\
| Evento | Payload | Consumidores |\
|---|---|---|\
| `cashflow.entry_created` | `{ id, nota_id, valor_bruto, imposto, valor_liquido, data }` | Futuro: módulo de relatórios / DRE |\
| `cashflow.expense_created` | `{ id, descricao, valor, data }` | Futuro: módulo de relatórios |\
\
**Diagrama de Dados — Transação Financeira**\
```mermaid\
erDiagram\
TRANSACAO_FINANCEIRA {\
int id PK\
string tipo\
float valor_bruto\
float imposto\
float valor_liquido\
string descricao\
int nota_id FK\
datetime data_transacao\
datetime registrado_em\
}\
NOTA_FISCAL ||--o| TRANSACAO_FINANCEIRA : "origina"\
```\
\
**Exemplo — retorno de saldo**\
```json\
{\
"saldo_atual": 1500.00,\
"total_entradas": 2000.00,\
"total_saidas": 500.00,\
"total_impostos_recolhidos": 210.00\
}\
```\
\
---\
\
### 6. User Stories\
\
> *"Como Lojista, eu quero visualizar o saldo financeiro atual para saber se a empresa está lucrando."*\
\
> *"Como Contador, eu quero filtrar o extrato por período para conciliar todas as vendas e impostos do mês."*\
\
---\
\
### 7. Critérios de Aceite\
\
- [ ] Toda venda confirmada gera automaticamente uma entrada financeira\
- [ ] É possível registrar manualmente uma despesa com descrição e valor\
- [ ] O sistema exibe o saldo atual (entradas − saídas)\
- [ ] É possível filtrar o extrato por período (data início / data fim)\
- [ ] O extrato exibe: data, tipo, descrição, valor e saldo acumulado\
\
---\
\
### 8. Definição de Pronto (DoD)\
\
- [ ] Código revisado por outro membro do Squad\
- [ ] Testes unitários com >80% de cobertura\
- [ ] Documentação da API atualizada (Swagger/OpenAPI)\
- [ ] Pipeline de CI/CD passando\
- [ ] Integração com MOD3 validada: nota gerada → entrada financeira criada automaticamente
