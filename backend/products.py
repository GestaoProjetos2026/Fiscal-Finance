# src/products.py
from flask import Blueprint, request, jsonify
from database import get_connection

# Um Blueprint é como uma "seção" da API, agrupa rotas relacionadas
products_bp = Blueprint("products", __name__)


# ─────────────────────────────────────────────────────────
# TASK #210 — GET /products (listar todos os produtos)
# ─────────────────────────────────────────────────────────
@products_bp.route("/products", methods=["GET"])
def listar_produtos():
    """
    Retorna a lista de todos os produtos cadastrados, incluindo o saldo de estoque.
    Opcional: filtrar por nome com ?nome=caneta
    Exemplo de URL: GET /v1/fisc/products?nome=caneta
    """
    filtro_nome = request.args.get("nome", "")  # pega o ?nome= da URL, se houver

    conn = get_connection()
    cursor = conn.cursor()

    # JOIN com subquery que calcula saldo: SUM(entradas) - SUM(saidas)
    query = """
        SELECT
            p.*,
            COALESCE(
                (SELECT SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END)
                 FROM estoque WHERE sku = p.sku),
            0) AS saldo_estoque
        FROM produtos p
    """

    if filtro_nome:
        cursor.execute(query + " WHERE p.nome LIKE ?", (f"%{filtro_nome}%",))
    else:
        cursor.execute(query)

    produtos = cursor.fetchall()
    conn.close()

    lista = [dict(p) for p in produtos]

    return jsonify({
        "status": "success",
        "data": lista,
        "message": f"{len(lista)} produto(s) encontrado(s)"
    }), 200


# ─────────────────────────────────────────────────────────
# TASK #211 — GET /products/{id} (buscar produto por SKU)
# ─────────────────────────────────────────────────────────
@products_bp.route("/products/<string:sku>", methods=["GET"])
def buscar_produto(sku):
    """
    Retorna um único produto pelo SKU, incluindo o saldo de estoque.
    Retorna 404 se não encontrado.
    Exemplo de URL: GET /v1/fisc/products/PROD-001
    """
    conn = get_connection()
    cursor = conn.cursor()

    # JOIN com subquery que calcula saldo: SUM(entradas) - SUM(saidas)
    cursor.execute("""
        SELECT
            p.*,
            COALESCE(
                (SELECT SUM(CASE WHEN tipo = 'entrada' THEN quantidade ELSE -quantidade END)
                 FROM estoque WHERE sku = p.sku),
            0) AS saldo_estoque
        FROM produtos p
        WHERE p.sku = ?
    """, (sku,))
    produto = cursor.fetchone()
    conn.close()

    if produto is None:
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


# ─────────────────────────────────────────────────────────
# TASK #209 + #214 — POST /products (criar produto + validar SKU único)
# ─────────────────────────────────────────────────────────
@products_bp.route("/products", methods=["POST"])
def criar_produto():
    """
    Cria um novo produto.
    Corpo da requisição (JSON):
    {
        "sku": "PROD-001",
        "nome": "Caneta Azul",
        "preco_base": 2.50,
        "aliquota_imposto": 0.12
    }
    """
    dados = request.get_json()

    # Validação 1: verificar se o corpo veio correto
    if not dados:
        return jsonify({
            "status": "error",
            "data": None,
            "message": "Corpo da requisição inválido. Envie um JSON válido."
        }), 400

    sku      = dados.get("sku",              "").strip()
    nome     = dados.get("nome",             "").strip()
    preco    = dados.get("preco_base")
    aliquota = dados.get("aliquota_imposto")  # aceita 'aliquota_imposto' do frontend
    if aliquota is None:
        aliquota = dados.get("aliquota")        # aceita 'aliquota' direto também

    # Validação 2: campos obrigatórios e regras de negócio
    if not sku:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'sku' é obrigatório."}), 400
    if not nome:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'nome' é obrigatório."}), 400
    if preco is None or preco <= 0:
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'preco_base' deve ser maior que 0."}), 400
    if aliquota is None or not (0 <= aliquota <= 1):
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'aliquota_imposto' deve ser entre 0 e 1."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # TASK #214 — Validação de SKU único: retorna 409 Conflict se já existir
    cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
    if cursor.fetchone():
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' já existe. O SKU deve ser único."
        }), 409

    # Tudo válido: salvar no banco
    cursor.execute(
        "INSERT INTO produtos (sku, nome, preco_base, aliquota) VALUES (?, ?, ?, ?)",
        (sku, nome, preco, aliquota)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "sku": sku,
            "nome": nome,
            "preco_base": preco,
            "aliquota_imposto": aliquota   # devolve com nome do frontend
        },
        "message": "Produto criado com sucesso."
    }), 201


# ─────────────────────────────────────────────────────────
# TASK #212 — PUT /products/{id} (editar produto)
# ─────────────────────────────────────────────────────────
@products_bp.route("/products/<string:sku>", methods=["PUT"])
def editar_produto(sku):
    """
    Atualiza os dados de um produto existente.
    REGRA: O SKU é imutável — não pode ser alterado via PUT.
    Corpo (todos os campos são opcionais — só envie o que quer atualizar):
    {
        "nome": "Caneta Vermelha",
        "preco_base": 3.00,
        "aliquota_imposto": 0.15
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se o produto existe
    cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
    produto_atual = cursor.fetchone()

    if produto_atual is None:
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' não encontrado."
        }), 404

    dados = request.get_json()
    if not dados:
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": "Corpo da requisição inválido ou vazio."
        }), 400

    # Mantém o valor atual se o campo não foi enviado
    produto_dict  = dict(produto_atual)
    novo_nome     = dados.get("nome",             produto_dict["nome"]).strip()
    novo_preco    = dados.get("preco_base",       produto_dict["preco_base"])
    # aceita 'aliquota_imposto' (frontend) ou 'aliquota' (banco direto)
    nova_aliquota = dados.get("aliquota_imposto", dados.get("aliquota", produto_dict["aliquota"]))

    # Validações nos novos valores
    if not novo_nome:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'nome' não pode ser vazio."}), 400
    if novo_preco <= 0:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'preco_base' deve ser maior que 0."}), 400
    if not (0 <= nova_aliquota <= 1):
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": "Campo 'aliquota_imposto' deve ser entre 0 e 1."}), 400

    cursor.execute(
        "UPDATE produtos SET nome = ?, preco_base = ?, aliquota = ? WHERE sku = ?",
        (novo_nome, novo_preco, nova_aliquota, sku)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "data": {
            "sku": sku,
            "nome": novo_nome,
            "preco_base": novo_preco,
            "aliquota_imposto": nova_aliquota   # devolve com nome do frontend
        },
        "message": "Produto atualizado com sucesso."
    }), 200


# ─────────────────────────────────────────────────────────
# TASK #213 — DELETE /products/{id} (remover produto)
# ─────────────────────────────────────────────────────────
@products_bp.route("/products/<string:sku>", methods=["DELETE"])
def remover_produto(sku):
    """
    Remove um produto pelo SKU.
    REGRA: Não pode remover se o produto tiver movimentações de estoque vinculadas.
    Retorna 409 se houver estoque vinculado.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se o produto existe
    cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({
            "status": "error",
            "data": None,
            "message": f"Produto com SKU '{sku}' não encontrado."
        }), 404

    # Verificar se tem movimentações de estoque vinculadas
    cursor.execute("SELECT COUNT(*) FROM estoque WHERE sku = ?", (sku,))
    total_movimentacoes = cursor.fetchone()[0]

    if total_movimentacoes > 0:
        conn.close()
        return jsonify({
            "status": "error",
            "data": {"movimentacoes_vinculadas": total_movimentacoes},
            "message": (
                f"Não é possível remover: produto possui "
                f"{total_movimentacoes} movimentação(ões) de estoque vinculada(s)."
            )
        }), 409

    # Tudo ok, remover
    cursor.execute("DELETE FROM produtos WHERE sku = ?", (sku,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "data": None,
        "message": f"Produto '{sku}' removido com sucesso."
    }), 200
