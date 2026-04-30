# stock.py
from flask import Blueprint, request, jsonify
from database import get_connection
from datetime import datetime

stock_bp = Blueprint("stock", __name__)

@stock_bp.route("/stock/entry", methods=["POST"])
def entrada_estoque():
    dados = request.get_json()

    if not dados:
        return jsonify({"status": "error", "data": None, "message": "Envie um JSON válido."}), 400

    sku      = dados.get("sku", "").strip()
    quantidade = dados.get("quantidade")
    motivo   = dados.get("motivo", "")

    if not sku:
        return jsonify({"status": "error", "data": None, "message": "Campo 'sku' é obrigatório."}), 400
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"status": "error", "data": None, "message": "Campo 'quantidade' deve ser um inteiro maior que 0."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT sku, preco_base FROM produtos WHERE sku = ?", (sku,))
    produto = cursor.fetchone()
    if not produto:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": f"Produto '{sku}' não encontrado."}), 404

    preco_base = produto[1]
    custo_total = quantidade * preco_base
    
    from database import consultar_resumo_caixa
    caixa = consultar_resumo_caixa()
    if caixa["saldo"] < custo_total:
        conn.close()
        return jsonify({
            "status": "error",
            "data": {"saldo_caixa": caixa["saldo"], "custo_total": custo_total},
            "message": f"Fluxo de caixa insuficiente (R$ {caixa['saldo']:.2f}) para pagar esta compra (R$ {custo_total:.2f})."
        }), 422

    # Ajustado de `estoque` para `estoque_mov` e adicionado `data_mov`
    cursor.execute(
        "INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov) VALUES (?, 'entrada', ?, ?, ?)",
        (sku, quantidade, motivo, datetime.now().isoformat())
    )
    conn.commit()

    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END), 0)
        FROM estoque_mov WHERE sku = ?
    """, (sku,))
    saldo = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "status": "success",
        "data": {"sku": sku, "tipo": "entrada", "quantidade": quantidade, "motivo": motivo, "saldo_atual": saldo},
        "message": f"Entrada de {quantidade} unidade(s) registrada. Saldo atual: {saldo}."
    }), 201


@stock_bp.route("/stock/exit", methods=["POST"])
def saida_estoque():
    dados = request.get_json()

    if not dados:
        return jsonify({"status": "error", "data": None, "message": "Envie um JSON válido."}), 400

    sku      = dados.get("sku", "").strip()
    quantidade = dados.get("quantidade")
    motivo   = dados.get("motivo", "")

    if not sku:
        return jsonify({"status": "error", "data": None, "message": "Campo 'sku' é obrigatório."}), 400
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"status": "error", "data": None, "message": "Campo 'quantidade' deve ser um inteiro maior que 0."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "data": None, "message": f"Produto '{sku}' não encontrado."}), 404

    # Calcular saldo ANTES de registrar a saída (usando estoque_mov)
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END), 0)
        FROM estoque_mov WHERE sku = ?
    """, (sku,))
    saldo_atual = cursor.fetchone()[0]

    # Bloquear se não tiver saldo suficiente
    if saldo_atual < quantidade:
        conn.close()
        return jsonify({
            "status": "error",
            "data": {"saldo_atual": saldo_atual, "quantidade_solicitada": quantidade},
            "message": f"Estoque insuficiente. Saldo atual: {saldo_atual}."
        }), 422

    cursor.execute(
        "INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov) VALUES (?, 'saida', ?, ?, ?)",
        (sku, quantidade, motivo, datetime.now().isoformat())
    )
    conn.commit()

    saldo_novo = saldo_atual - quantidade
    conn.close()

    return jsonify({
        "status": "success",
        "data": {"sku": sku, "tipo": "saida", "quantidade": quantidade, "motivo": motivo, "saldo_atual": saldo_novo},
        "message": f"Saída de {quantidade} unidade(s) registrada. Saldo atual: {saldo_novo}."
    }), 201


@stock_bp.route("/stock/<string:sku>", methods=["GET"])
def consultar_saldo(sku):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT sku, nome FROM produtos WHERE sku = ?", (sku,))
    produto = cursor.fetchone()

    if not produto:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": f"Produto '{sku}' não encontrado."}), 404

    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END), 0)
        FROM estoque_mov WHERE sku = ?
    """, (sku,))
    saldo = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "status": "success",
        "data": {"sku": produto["sku"], "nome": produto["nome"], "saldo_atual": saldo},
        "message": "Saldo consultado com sucesso."
    }), 200


@stock_bp.route("/stock/<string:sku>/history", methods=["GET"])
def historico_movimentacoes(sku):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "data": None, "message": f"Produto '{sku}' não encontrado."}), 404

    # Ajustado `data_movimentacao` para `data_mov`
    cursor.execute("""
        SELECT id, sku, tipo, quantidade, motivo, data_mov
        FROM estoque_mov WHERE sku = ?
        ORDER BY data_mov DESC
    """, (sku,))

    movimentacoes = [dict(m) for m in cursor.fetchall()]
    conn.close()

    return jsonify({
        "status": "success",
        "data": movimentacoes,
        "message": f"{len(movimentacoes)} movimentação(ões) encontrada(s)."
    }), 200
