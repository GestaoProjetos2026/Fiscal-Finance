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

    saldo = entradas - despesas

    conn.close()

    return {
        "entradas": round(entradas, 2),
        "despesas": round(despesas, 2),
        "saldo": round(saldo, 2)
    }

def registrar_despesa(descricao, valor, data=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if data:
            cursor.execute(
                """
                INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro)
                VALUES ('despesa', ?, ?, ?)
                """,
                (descricao, valor, data)
            )
        else:
            cursor.execute(
                """
                INSERT INTO caixa (tipo, descricao, valor_liquido)
                VALUES ('despesa', ?, ?)
                """,
                (descricao, valor)
            )

        conn.commit()
        conn.close()

        return True, "Despesa registrada com sucesso."

    except Exception as e:
        return False, str(e)

def consultar_extrato_periodo(data_inicio, data_fim):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo, descricao, valor_liquido, data_registro
        FROM caixa
        WHERE date(data_registro) BETWEEN ? AND ?
        ORDER BY data_registro DESC
    """, (data_inicio, data_fim))

    resultados = cursor.fetchall()
    conn.close()

    return resultados

def consultar_resumo_financeiro():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), SUM(valor_liquido) FROM caixa WHERE tipo='entrada'")
    qtd_entradas, total_entradas = cursor.fetchone()
    qtd_entradas = qtd_entradas or 0
    total_entradas = total_entradas or 0

    cursor.execute("SELECT COUNT(*), SUM(valor_liquido) FROM caixa WHERE tipo='despesa'")
    qtd_despesas, total_despesas = cursor.fetchone()
    qtd_despesas = qtd_despesas or 0
    total_despesas = total_despesas or 0

    saldo = total_entradas - total_despesas

    ticket_entrada = total_entradas / qtd_entradas if qtd_entradas > 0 else 0
    ticket_despesa = total_despesas / qtd_despesas if qtd_despesas > 0 else 0

    conn.close()

    return {
        "total_entradas": round(total_entradas, 2),
        "total_despesas": round(total_despesas, 2),
        "saldo": round(saldo, 2),
        "qtd_entradas": qtd_entradas,
        "qtd_despesas": qtd_despesas,
        "ticket_medio_entrada": round(ticket_entrada, 2),
        "ticket_medio_despesa": round(ticket_despesa, 2)
    }
