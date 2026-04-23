import sqlite3
from datetime import datetime

DB_NAME = "app.db"

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

def init_db():
    """Cria as tabelas caso elas não existam."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Produtos (Módulo 1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            sku TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco_base REAL NOT NULL,
            aliquota REAL NOT NULL,
            estoque INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de Movimentação de Estoque (Módulo 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque_mov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            tipo TEXT, -- 'entrada' ou 'saida'
            quantidade INTEGER,
            data_mov TEXT,
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )
    ''')
    
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

# --------------- FUNÇÕES DE PRODUTO ---------------

def salvar_produto(sku, nome, preco, aliquota):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO produtos (sku, nome, preco_base, aliquota, estoque)
            VALUES (?, ?, ?, ?, COALESCE((SELECT estoque FROM produtos WHERE sku = ?), 0))
        ''', (sku, nome, preco, aliquota, sku))
        conn.commit()
        return True, "Produto salvo com sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def buscar_produto(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def excluir_produto(sku):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Verificar se o produto existe
        cursor.execute("SELECT sku FROM produtos WHERE sku = ?", (sku,))
        if not cursor.fetchone():
            return False, "Produto não encontrado!"
            
        # 2. Remover históricos para evitar problemas no fluxo de caixa (saldo negativo/muito alto)
        cursor.execute("DELETE FROM invoices WHERE sku = ?", (sku,))
        cursor.execute("DELETE FROM estoque_mov WHERE sku = ?", (sku,))
        
        # 3. Remover o produto
        cursor.execute("DELETE FROM produtos WHERE sku = ?", (sku,))
        
        conn.commit()
        return True, "Produto e seu histórico excluídos com sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        if 'conn' in locals():
            conn.close()

def listar_produtos():
    """Retorna a lista de todos os produtos cadastrados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sku, nome, preco_base, aliquota, estoque FROM produtos ORDER BY nome ASC")
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return [dict(row) for row in rows]
    return []

# --------------- FUNÇÕES DE ESTOQUE ---------------

def registrar_movimentacao(sku, tipo, qtd, motivo: str = ''):
    """TASK 215/216: Registra entrada ou saída de estoque.
    TASK 220: Aceita e persiste o motivo da movimentação."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Registra a movimentação com motivo
        cursor.execute('''
            INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov)
            VALUES (?, ?, ?, ?, ?)
        ''', (sku, tipo, qtd, motivo, datetime.now().isoformat()))
        
        # 2. Atualiza o saldo na tabela de produtos
        if tipo == "entrada":
            cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE sku = ?", (qtd, sku))
        else:
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE sku = ?", (qtd, sku))
            
        conn.commit()
        return True, f"Movimentação de {tipo} realizada!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def listar_historico_movimentacoes(sku: str = None):
    """Retorna todas as movimentações de estoque, mais recentes primeiro.
    Se 'sku' for informado, filtra apenas aquele produto."""
    conn = get_connection()
    cursor = conn.cursor()
    if sku:
        cursor.execute("""
            SELECT em.id, em.sku, p.nome, em.tipo, em.quantidade,
                   COALESCE(em.motivo, '') AS motivo, em.data_mov
            FROM estoque_mov em
            LEFT JOIN produtos p ON em.sku = p.sku
            WHERE em.sku = ?
            ORDER BY em.data_mov DESC
        """, (sku,))
    else:
        cursor.execute("""
            SELECT em.id, em.sku, p.nome, em.tipo, em.quantidade,
                   COALESCE(em.motivo, '') AS motivo, em.data_mov
            FROM estoque_mov em
            LEFT JOIN produtos p ON em.sku = p.sku
            ORDER BY em.data_mov DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def consultar_saldo_estoque(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT estoque FROM produtos WHERE sku = ?", (sku,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# --------------- FUNÇÕES FISCAIS (SUA PARTE) ---------------

def salvar_nota_fiscal(sku, qtd, total):
    """Registra a venda confirmada no banco de dados."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (sku, quantidade, total_nota, data_emissao, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (sku, qtd, total, datetime.now().isoformat(), "CONFIRMADA"))
        conn.commit()
        conn.close()
        return True, "Nota registrada no banco."
    except Exception as e:
        return False, str(e)

# --------------- FUNÇÕES DE CAIXA ---------------

def consultar_resumo_caixa():
    """Calcula o total de vendas (entradas) e movimentações."""
    conn = get_connection()
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

