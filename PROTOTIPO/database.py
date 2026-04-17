import sqlite3

DB_FILE = "app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabela 1: Produtos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        sku TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        preco_base REAL NOT NULL,
        aliquota_imposto REAL NOT NULL
    )
    """)
    
    # Tabela 2: Estoque (Histórico de Movimentações)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        tipo TEXT NOT NULL,  -- 'entrada' ou 'saida'
        quantidade INTEGER NOT NULL,
        data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sku) REFERENCES produtos(sku)
    )
    """)
    
    # Tabela 4: Caixa
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL, -- 'entrada' ou 'despesa'
        descricao TEXT NOT NULL,
        valor_liquido REAL NOT NULL,
        data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabela 5: Notas Fiscais — Header da intenção (MOD5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas_fiscais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_nota TEXT NOT NULL UNIQUE,
        descricao TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'rascunho',
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabela 6: Itens da Nota Fiscal (MOD5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_nota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nota_id INTEGER NOT NULL,
        sku TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_base REAL NOT NULL,
        aliquota REAL NOT NULL,
        valor_bruto REAL NOT NULL,
        valor_imposto REAL NOT NULL,
        valor_total REAL NOT NULL,
        FOREIGN KEY(nota_id) REFERENCES notas_fiscais(id),
        FOREIGN KEY(sku) REFERENCES produtos(sku)
    )
    """)

    conn.commit()
    conn.close()

# ----- MÓDULO 1: PRODUTOS -----
def salvar_produto(sku, nome, preco, aliquota):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO produtos (sku, nome, preco_base, aliquota_imposto) VALUES (?, ?, ?, ?)",
                       (sku, nome, preco, aliquota))
        conn.commit()
        conn.close()
        return True, "Produto salvo com sucesso."
    except Exception as e:
        return False, str(e)

def buscar_produto(sku):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE sku=?", (sku,))
    prod = cursor.fetchone()
    conn.close()
    if prod:
        return {"sku": prod[0], "nome": prod[1], "preco_base": prod[2], "aliquota": prod[3]}
    return None

# ----- MÓDULO 2: ESTOQUE -----
def registrar_movimentacao(sku, tipo, quantidade):
    # Validar se o produto existe
    if not buscar_produto(sku):
        return False, "Produto não encontrado."
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO estoque (sku, tipo, quantidade) VALUES (?, ?, ?)", (sku, tipo, quantidade))
    conn.commit()
    conn.close()
    return True, f"Movimentação de {tipo} registrada!"

def consultar_saldo_estoque(sku):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantidade) FROM estoque WHERE sku=? AND tipo='entrada'", (sku,))
    entradas = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(quantidade) FROM estoque WHERE sku=? AND tipo='saida'", (sku,))
    saidas = cursor.fetchone()[0] or 0
    conn.close()
    return entradas - saidas

# ----- MÓDULO 4: CAIXA -----
def consultar_resumo_caixa():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor_liquido) FROM caixa WHERE tipo='entrada'")
    entradas = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(valor_liquido) FROM caixa WHERE tipo='despesa'")
    despesas = cursor.fetchone()[0] or 0
    conn.close()
    return {
        "entradas": entradas,
        "despesas": despesas,
        "saldo": entradas - despesas
    }

# ----- MÓDULO 5: NOTA FISCAL -----
def criar_nota_fiscal(numero_nota, descricao):
    """Cria o header (intenção) de uma nova nota fiscal com status 'rascunho'."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notas_fiscais (numero_nota, descricao, status) VALUES (?, ?, 'rascunho')",
            (numero_nota, descricao)
        )
        conn.commit()
        nota_id = cursor.lastrowid
        conn.close()
        return True, nota_id, "Intenção de nota fiscal criada com sucesso."
    except Exception as e:
        return False, None, str(e)

def buscar_nota_por_numero(numero_nota):
    """Retorna os dados do header da nota fiscal ou None se não encontrada."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero_nota, descricao, status, data_criacao FROM notas_fiscais WHERE numero_nota=?", (numero_nota,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "numero_nota": row[1], "descricao": row[2], "status": row[3], "data_criacao": row[4]}
    return None

def listar_notas():
    """Retorna todas as notas fiscais cadastradas, da mais recente para a mais antiga."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero_nota, descricao, status, data_criacao FROM notas_fiscais ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "numero_nota": r[1], "descricao": r[2], "status": r[3], "data_criacao": r[4]}
        for r in rows
    ]

def validar_sku_para_nota(nota_id, sku):
    """
    Valida se um SKU pode ser adicionado a uma nota fiscal.
    Realiza 3 verificações em sequência:
      1. A nota deve estar com status 'rascunho'
      2. O SKU deve existir na tabela de produtos
      3. O SKU não pode já ter sido adicionado a esta nota (duplicado)
    Retorna (valido: bool, codigo: str, mensagem: str, dados_produto: dict | None)
    Códigos possíveis: 'OK', 'NOTA_EMITIDA', 'SKU_INEXISTENTE', 'SKU_DUPLICADO'
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Verificação 1: status da nota deve ser 'rascunho'
    cursor.execute("SELECT status FROM notas_fiscais WHERE id=?", (nota_id,))
    row = cursor.fetchone()
    if row and row[0] != 'rascunho':
        conn.close()
        return False, 'NOTA_EMITIDA', "Esta nota já foi emitida e não aceita novos itens.", None

    # Verificação 2: SKU deve existir em produtos
    cursor.execute("SELECT nome, preco_base, aliquota_imposto FROM produtos WHERE sku=?", (sku,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        return False, 'SKU_INEXISTENTE', f"SKU '{sku}' não encontrado na base de produtos (cadastre no Módulo 1).", None

    # Verificação 3: SKU não pode ser duplicado na mesma nota
    cursor.execute("SELECT id FROM itens_nota WHERE nota_id=? AND sku=?", (nota_id, sku))
    dup = cursor.fetchone()
    conn.close()
    if dup:
        return False, 'SKU_DUPLICADO', f"SKU '{sku}' já foi adicionado a esta nota. Edite a quantidade se necessário.", None

    dados_produto = {"nome": prod[0], "preco_base": prod[1], "aliquota": prod[2]}
    return True, 'OK', f"✅ SKU válido: {prod[0]} | Preço: R$ {prod[1]:.2f} | Alíquota: {prod[2]*100:.1f}%", dados_produto

def adicionar_item_nota(nota_id, sku, quantidade, preco_base, aliquota):
    """Calcula o imposto por item e insere na tabela itens_nota."""
    valor_bruto = round(preco_base * quantidade, 2)
    valor_imposto = round(preco_base * aliquota * quantidade, 2)
    valor_total = round(valor_bruto + valor_imposto, 2)
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO itens_nota
               (nota_id, sku, quantidade, preco_base, aliquota, valor_bruto, valor_imposto, valor_total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nota_id, sku, quantidade, preco_base, aliquota, valor_bruto, valor_imposto, valor_total)
        )
        conn.commit()
        conn.close()
        return True, {
            "valor_bruto": valor_bruto,
            "valor_imposto": valor_imposto,
            "valor_total": valor_total
        }, "Item adicionado com sucesso."
    except Exception as e:
        return False, None, str(e)

def listar_itens_nota(nota_id):
    """Retorna todos os itens de uma nota fiscal pelo seu ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT sku, quantidade, preco_base, aliquota, valor_bruto, valor_imposto, valor_total
           FROM itens_nota WHERE nota_id=?""",
        (nota_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "sku": r[0], "quantidade": r[1], "preco_base": r[2],
            "aliquota": r[3], "valor_bruto": r[4],
            "valor_imposto": r[5], "valor_total": r[6]
        }
        for r in rows
    ]

def calcular_totais_nota(nota_id):
    """Calcula e retorna os totais consolidados de todos os itens de uma nota fiscal."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT
               COUNT(*)          AS num_itens,
               SUM(quantidade)   AS total_qtd,
               SUM(valor_bruto)  AS total_bruto,
               SUM(valor_imposto) AS total_imposto,
               SUM(valor_total)  AS total_final
           FROM itens_nota WHERE nota_id=?""",
        (nota_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row and row[0] and row[0] > 0:
        return {
            "num_itens":     row[0],
            "total_qtd":     row[1],
            "total_bruto":   round(row[2], 2),
            "total_imposto": round(row[3], 2),
            "total_final":   round(row[4], 2)
        }
    return None
