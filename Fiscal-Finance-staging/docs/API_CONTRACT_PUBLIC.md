# API Pública — Squad FISC · Contrato de Integração

> **Versão:** 1.0 · **Sprint:** 3 · **Equipe:** Squad FISC  
> **Base URL:** `http://<servidor-professor>:5000`  
> **Documentação interativa:** `GET /docs`

---

## Autenticação

Todos os endpoints públicos exigem o header:

```
X-API-KEY: <sua-chave>
```

| Squad | Chave |
|---|---|
| Squad 1 — Core Engine & Auth | `FISC-PUBLIC-2026-SQUAD1` |
| Squad 3 — CRM | `FISC-PUBLIC-2026-SQUAD3` |
| Squad 4 — Service Desk | `FISC-PUBLIC-2026-SQUAD4` |
| Desenvolvimento | `FISC-PUBLIC-2026-DEV` |

**Resposta para chave inválida ou ausente:**
```json
{
  "status": "error",
  "data": null,
  "message": "Acesso negado. Informe uma API Key válida no header X-API-KEY."
}
```
HTTP Status: `403 Forbidden`

---

## Padrão de Resposta

Todos os endpoints seguem o mesmo envelope JSON:

```json
{
  "status": "success" | "error",
  "data": { ... } | null,
  "message": "Mensagem legível"
}
```

### Códigos HTTP utilizados

| Situação | Código |
|---|---|
| Sucesso com dados | `200 OK` |
| Recurso não encontrado | `404 Not Found` |
| API Key inválida ou ausente | `403 Forbidden` |
| Erro interno do servidor | `500 Internal Server Error` |

---

## Endpoints Disponíveis

---

### `GET /v1/public/fisc/products/{sku}`

Consulta um produto pelo SKU. Retorna dados básicos + saldo de estoque atual.

**Headers:**
```
X-API-KEY: FISC-PUBLIC-2026-SQUAD1
```

**Exemplo de Requisição:**
```
GET /v1/public/fisc/products/PROD-001
```

**Resposta de Sucesso (`200`):**
```json
{
  "status": "success",
  "data": {
    "sku": "PROD-001",
    "nome": "Caneta Azul",
    "preco_base": 2.50,
    "aliquota_imposto": 0.12,
    "saldo_estoque": 45
  },
  "message": "Produto encontrado."
}
```

**Resposta de Erro — Produto não encontrado (`404`):**
```json
{
  "status": "error",
  "data": null,
  "message": "Produto com SKU 'PROD-999' não encontrado."
}
```

---

### `GET /v1/public/fisc/stock/{sku}`

Consulta o saldo de estoque atual de um produto pelo SKU.

**Headers:**
```
X-API-KEY: FISC-PUBLIC-2026-SQUAD1
```

**Exemplo de Requisição:**
```
GET /v1/public/fisc/stock/PROD-001
```

**Resposta de Sucesso (`200`):**
```json
{
  "status": "success",
  "data": {
    "sku": "PROD-001",
    "nome": "Caneta Azul",
    "saldo_atual": 45,
    "ultima_movimentacao": "2026-04-23T18:00:00"
  },
  "message": "Saldo de estoque consultado."
}
```

**Resposta — Produto não encontrado (`404`):**
```json
{
  "status": "error",
  "data": null,
  "message": "Produto com SKU 'PROD-999' não encontrado."
}
```

---

### `GET /v1/public/fisc/cashflow/summary`

Retorna o resumo financeiro consolidado do Squad FISC: saldo atual, entradas, despesas e impostos.

**Headers:**
```
X-API-KEY: FISC-PUBLIC-2026-SQUAD1
```

**Exemplo de Requisição:**
```
GET /v1/public/fisc/cashflow/summary
```

**Resposta de Sucesso (`200`):**
```json
{
  "status": "success",
  "data": {
    "saldo_atual": 1520.00,
    "total_entradas": 3500.00,
    "total_despesas": 1980.00,
    "total_impostos": 420.00
  },
  "message": "Resumo financeiro gerado."
}
```

---

## Exemplo de Integração (Python)

```python
import requests

BASE_URL = "http://<servidor>:5000"
HEADERS  = {"X-API-KEY": "FISC-PUBLIC-2026-SQUAD1"}

# Consultar produto
resp = requests.get(f"{BASE_URL}/v1/public/fisc/products/PROD-001", headers=HEADERS)
print(resp.json())

# Consultar estoque
resp = requests.get(f"{BASE_URL}/v1/public/fisc/stock/PROD-001", headers=HEADERS)
print(resp.json())

# Resumo financeiro
resp = requests.get(f"{BASE_URL}/v1/public/fisc/cashflow/summary", headers=HEADERS)
print(resp.json())
```

---

## Exemplo de Integração (curl)

```bash
# Produto
curl -H "X-API-KEY: FISC-PUBLIC-2026-SQUAD1" \
     http://<servidor>:5000/v1/public/fisc/products/PROD-001

# Estoque
curl -H "X-API-KEY: FISC-PUBLIC-2026-SQUAD1" \
     http://<servidor>:5000/v1/public/fisc/stock/PROD-001

# Resumo financeiro
curl -H "X-API-KEY: FISC-PUBLIC-2026-SQUAD1" \
     http://<servidor>:5000/v1/public/fisc/cashflow/summary
```

---

## Limitações e SLA

- Endpoints são **somente leitura** (GET) — nenhum dado pode ser criado ou alterado via API pública
- Sem paginação na versão 1.0
- Dados em tempo real (sem cache)
- Ambiente de desenvolvimento: `http://localhost:5000`
