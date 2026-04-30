# src/cashflow.py
# FISC-MOD4: Fluxo de Caixa — Endpoints REST
# FISC-25: POST  /v1/fisc/cashflow/expense
# FISC-26: GET   /v1/fisc/cashflow/balance
# FISC-27: GET   /v1/fisc/cashflow/statement
#
# CORREÇÃO (30/04/2026): balance e statement passaram a ler SOMENTE a tabela `caixa`
# como fonte de verdade, eliminando dupla contagem que ocorria porque o invoice/confirm
# já insere uma linha em `caixa` ao confirmar a nota, e o código antigo também
# recalculava receita via estoque_mov (contando duas vezes a mesma venda).

from flask import Blueprint, request, jsonify
from database import get_connection
from datetime import datetime

cashflow_bp = Blueprint("cashflow", __name__)


# ─────────────────────────────────────────────────────────
# FISC-26 — GET /cashflow/balance (saldo atual)
# ─────────────────────────────────────────────────────────
@cashflow_bp.route("/cashflow/balance", methods=["GET"])
def consultar_saldo():
    """
    Retorna o saldo atual do caixa calculado em tempo real.
    Fonte única de verdade: tabela `caixa`.
      Receitas  = linhas com tipo = 'entrada'  (inseridas pelo invoice/confirm e futuras entradas manuais)
      Despesas  = linhas com tipo = 'despesa'  (manuais) + tipo = 'compra' (entrada de estoque)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Receitas totais (todas as entradas na tabela caixa)
    cursor.execute("""
        SELECT COALESCE(SUM(valor_liquido), 0)
        FROM caixa
        WHERE tipo = 'entrada'
    """)
    total_entradas = cursor.fetchone()[0]

    # Despesas manuais registradas
    cursor.execute("""
        SELECT COALESCE(SUM(valor_liquido), 0)
        FROM caixa
        WHERE tipo = 'despesa'
    """)
    despesas_manuais = cursor.fetchone()[0]

    # Custo das compras de estoque (registradas com tipo 'compra')
    cursor.execute("""
        SELECT COALESCE(SUM(valor_liquido), 0)
        FROM caixa
        WHERE tipo = 'compra'
    """)
    custo_compras = cursor.fetchone()[0]

    conn.close()

    total_despesas = despesas_manuais + custo_compras
    saldo = total_entradas - total_despesas

    return jsonify({
        "status": "success",
        "data": {
            "total_entradas":  round(total_entradas,  2),
            "total_despesas":  round(total_despesas,  2),
            "saldo_liquido":   round(saldo,            2),
            "detalhamento": {
                "receita_vendas":   round(total_entradas,   2),
                "despesas_manuais": round(despesas_manuais, 2),
                "custo_compras":    round(custo_compras,    2)
            }
        },
        "message": "Saldo calculado com sucesso."
    }), 200


# ─────────────────────────────────────────────────────────
# FISC-25 — POST /cashflow/expense (registrar despesa manual)
# ─────────────────────────────────────────────────────────
@cashflow_bp.route("/cashflow/expense", methods=["POST"])
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
def extrato_periodo():
    """
    Retorna todas as transações de caixa em um período.
    Params: ?from=YYYY-MM-DD&to=YYYY-MM-DD
    Fonte única: tabela `caixa` (entradas de vendas + despesas manuais + compras de estoque).
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

    # Todas as transações do período (fonte única: tabela caixa)
    cursor.execute("""
        SELECT id, tipo, descricao, valor_liquido, data_registro
        FROM caixa
        WHERE date(data_registro) BETWEEN ? AND ?
        ORDER BY data_registro DESC
    """, (data_inicio, data_fim))

    rows = cursor.fetchall()
    conn.close()

    transacoes = []
    total_entradas = 0.0
    total_despesas = 0.0

    # Labels amigáveis para exibição no frontend
    tipo_label = {
        'entrada': 'venda_estoque',
        'despesa': 'despesa_manual',
        'compra':  'compra_estoque',
    }

    for row in rows:
        r = dict(row)
        eh_entrada = r["tipo"] == "entrada"

        transacoes.append({
            "origem":        tipo_label.get(r["tipo"], r["tipo"]),
            "tipo":          "entrada" if eh_entrada else "despesa",
            "descricao":     r["descricao"],
            "valor_liquido": round(r["valor_liquido"], 2),
            "data_registro": r["data_registro"]
        })

        if eh_entrada:
            total_entradas += r["valor_liquido"]
        else:
            total_despesas += r["valor_liquido"]

    return jsonify({
        "status": "success",
        "data": {
            "periodo":           {"from": data_inicio, "to": data_fim},
            "subtotal_entradas": round(total_entradas, 2),
            "subtotal_despesas": round(total_despesas, 2),
            "saldo_periodo":     round(total_entradas - total_despesas, 2),
            "transacoes":        transacoes
        },
        "message": f"{len(transacoes)} transação(ões) encontrada(s) no período."
    }), 200
