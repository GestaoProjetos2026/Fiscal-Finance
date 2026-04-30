# src/estoque.py
import datetime
from flask import Blueprint, request, jsonify
from database import get_connection
from auth import requer_papel

estoque_bp = Blueprint("estoque", __name__)

@estoque_bp.route("/stock/entry", methods=["POST"])
@requer_papel("estoque.entrada")
def registrar_entrada():
    """
    Registra uma entrada manual de estoque.
    Body JSON esperado:
    {
        "sku": "PROD-001",
        "quantidade": 10,
        "motivo": "Compra de fornecedor X"
    }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "message": "Corpo da requisição vazio."}), 400

    sku = dados.get("sku", "").strip().upper()
    quantidade = dados.get("quantidade")
    motivo = dados.get("motivo", "Entrada manual de estoque").strip()

    if not sku:
        return jsonify({"status": "error", "message": "SKU é obrigatório."}), 400
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"status": "error", "message": "Quantidade deve ser um inteiro maior que 0."}), 400
    if not motivo:
        return jsonify({"status": "error", "message": "Motivo é obrigatório."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se produto existe
    cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": f"Produto com SKU '{sku}' não encontrado."}), 404

    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 1. Atualiza campo saldo_estoque (para manter retrocompatibilidade caso algo o utilize, embora `estoque` seja calculado dinamicamente em algumas views)
        cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE sku = ?", (quantidade, sku))
        
        # 2. Insere a movimentação
        cursor.execute("""
            INSERT INTO estoque (sku, tipo, quantidade, motivo, data_movimentacao)
            VALUES (?, 'entrada', ?, ?, ?)
        """, (sku, quantidade, motivo, agora))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": f"Erro interno ao registrar entrada: {str(e)}"}), 500

    conn.close()
    return jsonify({
        "status": "success",
        "message": f"Entrada de {quantidade} unidades registrada para o produto {sku}."
    }), 201
