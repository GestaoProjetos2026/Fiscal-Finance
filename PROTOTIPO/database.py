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
