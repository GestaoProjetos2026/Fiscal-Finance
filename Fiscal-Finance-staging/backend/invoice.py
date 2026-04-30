# src/invoice.py
# FISC-MOD5: Nota Fiscal — Endpoints REST
# FISC-22: POST /v1/fisc/invoice/intent    → calcula nota sem salvar
# FISC-23: POST /v1/fisc/invoice/confirm   → confirma nota, baixa estoque, registra no caixa
# FISC-24: GET  /v1/fisc/invoice/<numero>  → busca nota por número
# FISC-MOD2-02: RBAC em estoque (baixa via confirm)
# FISC-MOD2-03: RBAC em fiscal (invoice)

from flask import Blueprint, request, jsonify
from database import get_connection
from datetime import datetime
from auth import requer_papel

invoice_bp = Blueprint("invoice", __name__)


# ─────────────────────────────────────────────────────────
# FISC-22 — POST /invoice/intent (calcular intenção de nota)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/intent", methods=["POST"])
@requer_papel("fiscal.intent")
def calcular_intencao():
    """
    Calcula os valores de uma nota fiscal SEM salvar no banco.
    Body: { "itens": [{ "sku": "PROD-001", "quantidade": 2 }] }
    """
    dados = request.get_json()
    if not dados or "itens" not in dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo inválido. Envie: { \"itens\": [{\"sku\": ..., \"quantidade\": ...}] }"}), 400

    itens_req = dados["itens"]
    if not itens_req:
        return jsonify({"status": "error", "data": None,
                        "message": "A lista de itens não pode ser vazia."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    itens_calculados = []
    skus_invalidos   = []
    total_bruto      = 0.0
    total_imposto    = 0.0
    total_final      = 0.0

    for item in itens_req:
        sku = str(item.get("sku", "")).strip()
        qtd = item.get("quantidade", 0)

        if not sku or qtd <= 0:
            skus_invalidos.append({"sku": sku, "motivo": "SKU ou quantidade inválidos."})
            continue

        cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
        produto = cursor.fetchone()

        if not produto:
            skus_invalidos.append({"sku": sku, "motivo": "Produto não encontrado no cadastro."})
            continue

        p         = dict(produto)
        aliquota  = p.get("aliquota_imposto", 0)
        vb        = p["preco_base"] * qtd
        vi        = vb * aliquota
        vt        = vb + vi

        total_bruto   += vb
        total_imposto += vi
        total_final   += vt

        itens_calculados.append({
            "sku":            sku,
            "nome":           p["nome"],
            "quantidade":     qtd,
            "preco_unitario": p["preco_base"],
            "aliquota":       aliquota,
            "valor_bruto":    round(vb, 2),
            "valor_imposto":  round(vi, 2),
            "valor_total":    round(vt, 2)
        })

    conn.close()

    if skus_invalidos and not itens_calculados:
        return jsonify({
            "status": "error",
            "data":   {"skus_invalidos": skus_invalidos},
            "message": "Nenhum item válido encontrado."
        }), 422

    return jsonify({
        "status": "success",
        "data": {
            "itens":           itens_calculados,
            "skus_invalidos":  skus_invalidos,
            "totais": {
                "total_bruto":    round(total_bruto,   2),
                "total_imposto":  round(total_imposto, 2),
                "total_final":    round(total_final,   2)
            }
        },
        "message": "Intenção calculada. Use /invoice/confirm para confirmar."
    }), 200


# ─────────────────────────────────────────────────────────
# FISC-23 — POST /invoice/confirm (confirmar nota)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/confirm", methods=["POST"])
@requer_papel("fiscal.confirm", "estoque.saida")
def confirmar_nota():
    """
    Confirma a nota fiscal: valida estoque, baixa estoque, salva nota e registra no caixa.
    Operação atômica — usa transação única.
    Body: { "numero": "NF-2026-001", "descricao": "Venda loja", "itens": [...] }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo da requisição inválido."}), 400

    numero    = str(dados.get("numero", "")).strip()
    descricao = str(dados.get("descricao", "Nota confirmada via API")).strip()
    itens_req = dados.get("itens", [])

    if not numero:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'numero' é obrigatório."}), 400
    if not itens_req:
        return jsonify({"status": "error", "data": None,
                        "message": "A lista de itens não pode ser vazia."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se número já existe
    cursor.execute("SELECT id FROM notas_fiscais WHERE numero_nota = ?", (numero,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Nota '{numero}' já existe."}), 409

    # Valida e calcula todos os itens
    itens_validos = []
    skus_invalidos = []

    for item in itens_req:
        sku = str(item.get("sku", "")).strip()
        qtd = item.get("quantidade", 0)

        cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
        produto = cursor.fetchone()
        if not produto:
            skus_invalidos.append({"sku": sku, "motivo": "Produto não encontrado."})
            continue

        p = dict(produto)
        estoque_atual = p.get("estoque", 0)
        if estoque_atual < qtd:
            conn.close()
            return jsonify({
                "status": "error", "data": None,
                "message": f"Estoque insuficiente para SKU '{sku}'. Disponível: {estoque_atual}, necessário: {qtd}."
            }), 422

        aliquota = p.get("aliquota_imposto", 0)
        vb = p["preco_base"] * qtd
        vi = vb * aliquota
        vt = vb + vi
        itens_validos.append({**p, "quantidade": qtd, "aliquota": aliquota,
                               "vb": vb, "vi": vi, "vt": vt})

    if skus_invalidos:
        conn.close()
        return jsonify({
            "status": "error",
            "data":   {"skus_invalidos": skus_invalidos},
            "message": "Existem SKUs inválidos. Corrija e tente novamente."
        }), 422

    # Operação atômica
    try:
        agora = datetime.now().isoformat()

        # 1. Cria a nota
        cursor.execute(
            "INSERT INTO notas_fiscais (numero_nota, descricao, status, data_criacao) VALUES (?, ?, 'emitida', ?)",
            (numero, descricao, agora)
        )
        nota_id = cursor.lastrowid

        total_final = 0.0
        for item in itens_validos:
            # 2. Insere itens
            cursor.execute("""
                INSERT INTO itens_nota
                    (nota_id, sku, quantidade, preco_base, aliquota, valor_bruto, valor_imposto, valor_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nota_id, item["sku"], item["quantidade"], item["preco_base"],
                  item["aliquota"], item["vb"], item["vi"], item["vt"]))

            # 3. Baixa o estoque
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE sku = ?",
                (item["quantidade"], item["sku"])
            )
            cursor.execute("""
                INSERT INTO estoque (sku, tipo, quantidade, motivo, data_movimentacao)
                VALUES (?, 'saida', ?, ?, ?)
            """, (item["sku"], item["quantidade"], f"Emissão NF {numero}", agora))

            total_final += item["vt"]

        # 4. Registra entrada no caixa
        cursor.execute(
            "INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro) VALUES ('entrada', ?, ?, ?)",
            (f"Receita NF {numero}", total_final, agora)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "data": {
                "nota_id":     nota_id,
                "numero":      numero,
                "status":      "emitida",
                "total_final": round(total_final, 2),
                "itens":       len(itens_validos)
            },
            "message": f"Nota '{numero}' emitida com sucesso!"
        }), 201

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Erro interno ao confirmar nota: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────
# FISC-24 — GET /invoice/<numero> (buscar nota por número)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/<string:numero>", methods=["GET"])
@requer_papel("fiscal.ler")
def buscar_nota(numero):
    """
    Retorna uma nota fiscal com todos os seus itens e totais.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notas_fiscais WHERE numero_nota = ?", (numero,))
    nota = cursor.fetchone()

    if not nota:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Nota '{numero}' não encontrada."}), 404

    nota_dict = dict(nota)

    cursor.execute("""
        SELECT i.*, p.nome
        FROM itens_nota i
        JOIN produtos p ON i.sku = p.sku
        WHERE i.nota_id = ?
        ORDER BY i.id ASC
    """, (nota_dict["id"],))
    itens = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) AS total FROM itens_nota WHERE nota_id = ?
    """, (nota_dict["id"],))
    total = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "nota":   nota_dict,
            "itens":  itens,
            "totais": {"total_final": round(total, 2), "num_itens": len(itens)}
        },
        "message": "Nota encontrada."
    }), 200
