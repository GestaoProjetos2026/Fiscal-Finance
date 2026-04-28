from flask import Blueprint, jsonify, request
from database import get_connection
from auth import requer_auth

integration_bp = Blueprint("integration", __name__)

# FISC-MOD1-02 — Integração com CRM (Consulta de Estoque)
@integration_bp.route("/integration/crm/stock/<string:sku>", methods=["GET"])
def crm_consulta_estoque(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nome, 
        COALESCE((SELECT SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END) 
                  FROM estoque WHERE sku = p.sku), 0) AS saldo
        FROM produtos p WHERE p.sku = ?
    """, (sku,))
    res = cursor.fetchone()
    conn.close()
    if not res:
        return jsonify({"status": "error", "message": "Produto não encontrado"}), 404
    return jsonify({"status": "success", "sku": sku, "saldo": res["saldo"]})

# FISC-MOD1-03 — Integração com Service Desk (Histórico)
@integration_bp.route("/integration/sd/history/<int:usuario_id>", methods=["GET"])
@requer_auth
def sd_historico_cliente(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notas_fiscais WHERE id_usuario = ? ORDER BY data_criacao DESC", (usuario_id,))
    notas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "historico": notas})
