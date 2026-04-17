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
    
    # Tabela de Notas Fiscais (Módulo 3 - Sua parte)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            quantidade INTEGER,
            total_nota REAL,
            data_emissao TEXT,
            status TEXT,
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )
    ''')
    
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

def registrar_movimentacao(sku, tipo, qtd):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Registra a movimentação
        cursor.execute('''
            INSERT INTO estoque_mov (sku, tipo, quantidade, data_mov)
            VALUES (?, ?, ?, ?)
        ''', (sku, tipo, qtd, datetime.now().isoformat()))
        
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
    
    # Soma total das Entradas (Receitas): todas as saídas de estoque (vendas)
    cursor.execute("""
        SELECT SUM(e.quantidade * p.preco_base * 1.18) 
        FROM estoque_mov e 
        JOIN produtos p ON e.sku = p.sku 
        WHERE e.tipo = 'saida'
    """)
    total_vendas = cursor.fetchone()[0]
    if total_vendas is None:
        total_vendas = 0.0
    
    # Saídas (Despesas): Custo das compras de estoque (Entradas de estoque)
    cursor.execute("""
        SELECT SUM(e.quantidade * p.preco_base) 
        FROM estoque_mov e 
        JOIN produtos p ON e.sku = p.sku 
        WHERE e.tipo = 'entrada'
    """)
    total_saidas = cursor.fetchone()[0]
    if total_saidas is None:
        total_saidas = 0.0
    
    conn.close()
    return {
        "entradas": total_vendas,
        "despesas": total_saidas,
        "saldo": total_vendas - total_saidas
    }

# --------------- MIGRAÇÕES ---------------

def _run_migrations():
    """Adiciona as colunas necessárias sem quebrar as tabelas já existentes."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Adaptado de 'estoque' para 'estoque_mov' conforme a estrutura atual
        cursor.execute("ALTER TABLE estoque_mov ADD COLUMN motivo TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # Se o campo já existe, ignora o erro
    finally:
        conn.close()

# Roda as migrações automaticamente ao carregar o database.py
_run_migrations()
