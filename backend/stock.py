# src/stock.py
# FISC-19 (Sprint 2) — POST /v1/fisc/stock/entry
# Endpoint de entrada de estoque — registra compra/reposição de mercadoria.
# Implementado na versão web em 30/04/2026 (tarefa que estava pendente desde Sprint 2).
#
# Fluxo:
#   1. Valida que SKU existe
#   2. Atualiza produtos.estoque += quantidade
#   3. Registra log em estoque_mov (tipo='entrada')
#   4. Registra custo na tabela caixa (tipo='compra') para impactar o fluxo de caixa

from flask import Blueprint, request, jsonify
from database import get_connection
from datetime import datetime
from auth import requer_papel

stock_bp = Blueprint("stock", __name__)


@stock_bp.route("/stock/entry", methods=["POST"])
@requer_papel(["admin", "gerente"])
def entrada_estoque():
    """
    Registra entrada de estoque (compra/reposição).
    Body: { "sku": "PROD-001", "quantidade": 10, "motivo": "Compra fornecedor X" }
    Impacto: aumenta produtos.estoque, registra em estoque_mov e lança despesa de compra no caixa.
    """
    dados = request.get_json()

    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Envie um JSON válido."}), 400

    sku       = str(dados.get("sku", "")).strip().upper()
    quantidade = dados.get("quantidade")
    motivo    = str(dados.get("motivo", "Entrada de estoque")).strip()

    # Validações
    if not sku:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'sku' é obrigatório."}), 400

    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'quantidade' deve ser um número inteiro maior que 0."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se produto existe
    cursor.execute("SELECT sku, nome, preco_base, estoque FROM produtos WHERE sku = ?", (sku,))
    produto = cursor.fetchone()

    if not produto:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Produto '{sku}' não encontrado no cadastro."}), 404

    p          = dict(produto)
    custo_total = round(quantidade * p["preco_base"], 2)
    agora      = datetime.now().isoformat()

    try:
        # 1. Atualiza saldo no produto
        cursor.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE sku = ?",
            (quantidade, sku)
        )

        # 2. Registra log de movimentação
        cursor.execute(
            "INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov) VALUES (?, 'entrada', ?, ?, ?)",
            (sku, quantidade, motivo, agora)
        )

        # 3. Lança custo da compra no caixa (tipo='compra' para diferenciar de 'despesa' manual)
        cursor.execute(
            "INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro) VALUES ('compra', ?, ?, ?)",
            (f"Compra: {p['nome']} ({sku}) — {quantidade} un.", custo_total, agora)
        )

        conn.commit()

        # Busca saldo atualizado
        cursor.execute("SELECT estoque FROM produtos WHERE sku = ?", (sku,))
        saldo_atual = cursor.fetchone()["estoque"]
        conn.close()

        return jsonify({
            "status": "success",
            "data": {
                "sku":         sku,
                "nome":        p["nome"],
                "tipo":        "entrada",
                "quantidade":  quantidade,
                "motivo":      motivo,
                "custo_total": custo_total,
                "saldo_atual": saldo_atual
            },
            "message": f"Entrada de {quantidade} unidade(s) de '{p['nome']}' registrada. Saldo atual: {saldo_atual}."
        }), 201

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Erro interno ao registrar entrada: {str(e)}"}), 500
