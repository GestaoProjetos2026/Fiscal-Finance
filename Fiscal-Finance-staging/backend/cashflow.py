# src/cashflow.py
# FISC-MOD2 Sprint 2 — Autenticação JWT
# FISC-25: POST  /v1/fisc/cashflow/expense
# FISC-26: GET   /v1/fisc/cashflow/balance
# FISC-27: GET   /v1/fisc/cashflow/statement
# FISC-MOD2-04: RBAC em caixa

from flask import Blueprint, request, jsonify
from database import get_connection
from datetime import datetime
from auth import requer_papel

cashflow_bp = Blueprint("cashflow", __name__)


# ─────────────────────────────────────────────────────────
# FISC-26 — GET /cashflow/balance (saldo atual)
# ─────────────────────────────────────────────────────────
@cashflow_bp.route("/cashflow/balance", methods=["GET"])
@requer_papel("caixa.ler")
def consultar_saldo():
    """
    Retorna o saldo atual do caixa calculado em tempo real.
    Receitas  = saídas de estoque (vendas)   × preco_base × 1.18
    Despesas  = entradas manuais na tabela caixa + compras de estoque × preco_base
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Receitas: vendas (saídas de estoque)
    cursor.execute("""
        SELECT COALESCE(SUM(e.quantidade * p.preco_base * 1.18), 0)
        FROM estoque e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'saida'
    """)
    total_vendas = cursor.fetchone()[0]

    # Despesas manuais registradas na tabela caixa
    cursor.execute("""
        SELECT COALESCE(SUM(valor_liquido), 0)
        FROM caixa
        WHERE tipo = 'despesa'
    """)
    despesas_manuais = cursor.fetchone()[0]

    # Custo das compras (entradas de estoque)
    cursor.execute("""
        SELECT COALESCE(SUM(e.quantidade * p.preco_base), 0)
        FROM estoque e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'entrada'
    """)
    custo_compras = cursor.fetchone()[0]

    conn.close()

    total_despesas = despesas_manuais + custo_compras
    saldo = total_vendas - total_despesas

    return jsonify({
        "status": "success",
        "data": {
            "total_entradas":  round(total_vendas,    2),
            "total_despesas":  round(total_despesas,  2),
            "saldo_liquido":   round(saldo,            2),
            "detalhamento": {
                "receita_vendas":   round(total_vendas,   2),
                "despesas_manuais": round(despesas_manuais, 2),
                "custo_compras":    round(custo_compras,  2)
            }
        },
        "message": "Saldo calculado com sucesso."
    }), 200


# ─────────────────────────────────────────────────────────
# FISC-25 — POST /cashflow/expense (registrar despesa manual)
# ─────────────────────────────────────────────────────────
@cashflow_bp.route("/cashflow/expense", methods=["POST"])
@requer_papel("caixa.despesa")
def registrar_despesa():
    """
    Registra uma despesa manual no caixa.
    Body: { "descricao": "Aluguel", "valor": 1200.00, "data": "2026-04-23" }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo da requisição inválido."}), 400

    descricao = dados.get("descricao", "").strip()
    valor     = dados.get("valor")
    data      = dados.get("data")  # opcional

    if not descricao:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'descricao' é obrigatório."}), 400
    if valor is None or valor <= 0:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'valor' deve ser maior que 0."}), 400

    # Valida data se fornecida
    if data:
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            return jsonify({"status": "error", "data": None,
                            "message": "Campo 'data' deve estar no formato YYYY-MM-DD."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    if data:
        cursor.execute(
            "INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro) VALUES ('despesa', ?, ?, ?)",
            (descricao, valor, data)
        )
    else:
        cursor.execute(
            "INSERT INTO caixa (tipo, descricao, valor_liquido) VALUES ('despesa', ?, ?)",
            (descricao, valor)
        )

    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "id":        novo_id,
            "tipo":      "despesa",
            "descricao": descricao,
            "valor":     valor,
            "data":      data or datetime.now().strftime("%Y-%m-%d")
        },
        "message": "Despesa registrada com sucesso."
    }), 201


# ─────────────────────────────────────────────────────────
# FISC-27 — GET /cashflow/statement (extrato por período)
# ─────────────────────────────────────────────────────────
@cashflow_bp.route("/cashflow/statement", methods=["GET"])
@requer_papel("caixa.ler")
def extrato_periodo():
    """
    Retorna todas as transações de caixa em um período.
    Params: ?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    data_inicio = request.args.get("from")
    data_fim    = request.args.get("to")

    if not data_inicio or not data_fim:
        return jsonify({"status": "error", "data": None,
                        "message": "Parâmetros 'from' e 'to' são obrigatórios. Ex: ?from=2026-01-01&to=2026-12-31"}), 400

    try:
        datetime.strptime(data_inicio, "%Y-%m-%d")
        datetime.strptime(data_fim,    "%Y-%m-%d")
    except ValueError:
        return jsonify({"status": "error", "data": None,
                        "message": "Datas devem estar no formato YYYY-MM-DD."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Despesas manuais no período
    cursor.execute("""
        SELECT 'despesa_manual' AS origem, tipo, descricao, valor_liquido, data_registro
        FROM caixa
        WHERE date(data_registro) BETWEEN ? AND ?
        ORDER BY data_registro DESC
    """, (data_inicio, data_fim))
    despesas = [dict(row) for row in cursor.fetchall()]

    # Movimentações de estoque no período
    cursor.execute("""
        SELECT
            e.tipo                                       AS origem_tipo,
            p.nome                                       AS descricao,
            e.quantidade * p.preco_base * 1.18           AS valor_venda,
            e.quantidade * p.preco_base                  AS valor_custo,
            e.data_movimentacao                          AS data_registro,
            e.sku
        FROM estoque e
        JOIN produtos p ON e.sku = p.sku
        WHERE date(e.data_movimentacao) BETWEEN ? AND ?
        ORDER BY e.data_movimentacao DESC
    """, (data_inicio, data_fim))

    movs = []
    total_entradas = 0.0
    total_despesas = 0.0

    for row in cursor.fetchall():
        r = dict(row)
        if r["origem_tipo"] == "saida":
            movs.append({
                "origem": "venda_estoque",
                "tipo": "entrada",
                "descricao": f"Venda: {r['descricao']} ({r['sku']})",
                "valor_liquido": round(r["valor_venda"], 2),
                "data_registro": r["data_registro"]
            })
            total_entradas += r["valor_venda"]
        else:
            movs.append({
                "origem": "compra_estoque",
                "tipo": "despesa",
                "descricao": f"Compra: {r['descricao']} ({r['sku']})",
                "valor_liquido": round(r["valor_custo"], 2),
                "data_registro": r["data_registro"]
            })
            total_despesas += r["valor_custo"]

    for d in despesas:
        total_despesas += d["valor_liquido"]

    conn.close()

    todas = movs + despesas
    todas.sort(key=lambda x: x["data_registro"], reverse=True)

    return jsonify({
        "status": "success",
        "data": {
            "periodo":         {"from": data_inicio, "to": data_fim},
            "subtotal_entradas": round(total_entradas, 2),
            "subtotal_despesas": round(total_despesas, 2),
            "saldo_periodo":     round(total_entradas - total_despesas, 2),
            "transacoes":        todas
        },
        "message": f"{len(todas)} transação(ões) encontrada(s) no período."
    }), 200
