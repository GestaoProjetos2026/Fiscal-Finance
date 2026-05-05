# src/public_api.py
# FISC-MOD3-01 — Endpoints Públicos Inter-Squads
# Sprint 3 · Squad FISC
#
# Autenticação: header obrigatório → X-API-KEY: <chave>
# Padrão de resposta: { "status": "success"|"error", "data": {...}|null, "message": "..." }
#
# GET /v1/public/fisc/products/<sku>       → Consulta produto por SKU
# GET /v1/public/fisc/stock/<sku>          → Saldo de estoque por SKU
# GET /v1/public/fisc/cashflow/summary     → Resumo financeiro geral

from flask import Blueprint, request, jsonify
from database import get_connection

public_bp = Blueprint("public", __name__)

# ── Chaves de API autorizadas ────────────────────────────────────
# Em produção: mover para variável de ambiente ou tabela no banco
VALID_API_KEYS = {
    "FISC-PUBLIC-2026-SQUAD1",   # Squad 1 — Core Engine & Auth
    "FISC-PUBLIC-2026-SQUAD3",   # Squad 3 — CRM
    "FISC-PUBLIC-2026-SQUAD4",   # Squad 4 — Service Desk
    "FISC-PUBLIC-2026-DEV",      # Ambiente de desenvolvimento
}


def _validar_api_key() -> bool:
    """Valida o header X-API-KEY. Retorna True se autorizado."""
    chave = request.headers.get("X-API-KEY", "")
    return chave in VALID_API_KEYS


def _erro_nao_autorizado():
    return jsonify({
        "status": "error",
        "data": None,
        "message": "Acesso negado. Informe uma API Key válida no header X-API-KEY."
    }), 403


# ────────────────────────────────────────────────────────────────
# GET /v1/public/fisc/products/<sku>
# Retorna produto por SKU — somente leitura, sem dados sensíveis
# ────────────────────────────────────────────────────────────────
@public_bp.route("/public/fisc/products/<string:sku>", methods=["GET"])
def produto_publico(sku):
    """
    Consulta pública de produto por SKU.
    Requer header: X-API-KEY: <chave>

    Resposta:
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
    """
    if not _validar_api_key():
        return _erro_nao_autorizado()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.sku,
            p.nome,
            p.preco_base,
            COALESCE(p.aliquota, p.aliquota_imposto, 0) AS aliquota_imposto,
            COALESCE(
                (SELECT SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END)
                 FROM estoque_mov WHERE sku = p.sku),
            0) AS saldo_estoque
        FROM produtos p
        WHERE p.sku = ?
    """, (sku,))

    produto = cursor.fetchone()
    conn.close()

    if not produto:
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' não encontrado."
        }), 404

    return jsonify({
        "status": "success",
        "data": dict(produto),
        "message": "Produto encontrado."
    }), 200


# ────────────────────────────────────────────────────────────────
# GET /v1/public/fisc/stock/<sku>
# Retorna saldo de estoque atual por SKU
# ────────────────────────────────────────────────────────────────
@public_bp.route("/public/fisc/stock/<string:sku>", methods=["GET"])
def estoque_publico(sku):
    """
    Consulta pública do saldo de estoque por SKU.
    Requer header: X-API-KEY: <chave>

    Resposta:
    {
      "status": "success",
      "data": {
        "sku": "PROD-001",
        "nome": "Caneta Azul",
        "saldo_atual": 45,
        "ultima_movimentacao": "2026-04-23T12:00:00"
      },
      "message": "Saldo de estoque consultado."
    }
    """
    if not _validar_api_key():
        return _erro_nao_autorizado()

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se produto existe
    cursor.execute("SELECT sku, nome FROM produtos WHERE sku = ?", (sku,))
    produto = cursor.fetchone()

    if not produto:
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' não encontrado."
        }), 404

    # Calcula saldo
    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END), 0) AS saldo_atual,
            MAX(data_mov) AS ultima_movimentacao
        FROM estoque_mov
        WHERE sku = ?
    """, (sku,))
    estoque = cursor.fetchone()
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "sku":                 produto["sku"],
            "nome":                produto["nome"],
            "saldo_atual":         estoque["saldo_atual"] if estoque else 0,
            "ultima_movimentacao": estoque["ultima_movimentacao"] if estoque else None
        },
        "message": "Saldo de estoque consultado."
    }), 200


# ────────────────────────────────────────────────────────────────
# GET /v1/public/fisc/cashflow/summary
# Retorna resumo financeiro consolidado do Squad FISC
# ────────────────────────────────────────────────────────────────
@public_bp.route("/public/fisc/cashflow/summary", methods=["GET"])
def resumo_caixa_publico():
    """
    Resumo financeiro público do Squad FISC.
    Requer header: X-API-KEY: <chave>

    Resposta:
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
    """
    if not _validar_api_key():
        return _erro_nao_autorizado()

    conn = get_connection()
    cursor = conn.cursor()

    # Receitas: vendas (saídas de estoque × preço × 1.18 inclui imposto)
    cursor.execute("""
        SELECT COALESCE(SUM(e.quantidade * p.preco_base), 0)              AS receita_bruta,
               COALESCE(SUM(e.quantidade * p.preco_base *
                   COALESCE(p.aliquota, p.aliquota_imposto, 0)), 0)       AS total_impostos
        FROM estoque_mov e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'saida'
    """)
    vendas = cursor.fetchone()

    # Despesas: compras (entradas de estoque) + despesas manuais
    cursor.execute("""
        SELECT COALESCE(SUM(e.quantidade * p.preco_base), 0) AS custo_compras
        FROM estoque_mov e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'entrada'
    """)
    compras = cursor.fetchone()

    cursor.execute("""
        SELECT COALESCE(SUM(valor_liquido), 0) AS despesas_manuais
        FROM caixa WHERE tipo = 'despesa'
    """)
    despesas_manuais = cursor.fetchone()
    conn.close()

    receita_bruta   = vendas["receita_bruta"]   if vendas else 0
    total_impostos  = vendas["total_impostos"]   if vendas else 0
    total_entradas  = receita_bruta + total_impostos  # preço final com imposto
    custo_compras   = compras["custo_compras"]        if compras else 0
    desp_manuais    = despesas_manuais["despesas_manuais"] if despesas_manuais else 0
    total_despesas  = custo_compras + desp_manuais
    saldo_atual     = total_entradas - total_despesas

    return jsonify({
        "status": "success",
        "data": {
            "saldo_atual":     round(saldo_atual,    2),
            "total_entradas":  round(total_entradas, 2),
            "total_despesas":  round(total_despesas, 2),
            "total_impostos":  round(total_impostos, 2)
        },
        "message": "Resumo financeiro gerado."
    }), 200
# ────────────────────────────────────────────────────────────────
# GET /v1/public/fisc/history/<string:sku>
# FISC-MOD1-03 — Retorna histórico de movimentações para Service Desk
# ────────────────────────────────────────────────────────────────
@public_bp.route("/public/fisc/history/<string:sku>", methods=["GET"])
def historico_publico(sku):
    """
    Consulta pública do histórico de movimentações por SKU.
    Requer header: X-API-KEY: <chave>
    """
    if not _validar_api_key():
        return _erro_nao_autorizado()

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se o produto existe
    cursor.execute("SELECT sku, nome FROM produtos WHERE sku = ?", (sku,))
    produto = cursor.fetchone()

    if not produto:
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' não encontrado."
        }), 404

    # Busca todas as movimentações (entrada e saída)
    cursor.execute("""
        SELECT tipo, quantidade, motivo, data_mov
        FROM estoque_mov
        WHERE sku = ?
        ORDER BY data_mov DESC
    """, (sku,))
    
    historico = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "sku": produto["sku"],
            "nome": produto["nome"],
            "historico": historico
        },
        "message": "Histórico de movimentações consultado com sucesso."
    }), 200
