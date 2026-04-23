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
            motivo TEXT,
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

    # Migração: corrige o schema do banco já existente
    _migrar_banco()

def _migrar_banco():
    """
    Detecta e corrige incompatibilidades de schema no app.db existente.
    Executada sempre após init_db() — é segura e idempotente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Tabela: produtos ──────────────────────────────────────────────
    cursor.execute("PRAGMA table_info(produtos)")
    colunas_produtos = {row['name'] for row in cursor.fetchall()}

    # Caso 1: coluna antiga era 'aliquota_imposto' → renomear para 'aliquota'
    if 'aliquota_imposto' in colunas_produtos and 'aliquota' not in colunas_produtos:
        cursor.execute("ALTER TABLE produtos RENAME COLUMN aliquota_imposto TO aliquota")

    # Caso 2: nem 'aliquota' nem 'aliquota_imposto' existem → adicionar
    cursor.execute("PRAGMA table_info(produtos)")
    colunas_produtos = {row['name'] for row in cursor.fetchall()}
    if 'aliquota' not in colunas_produtos:
        cursor.execute("ALTER TABLE produtos ADD COLUMN aliquota REAL NOT NULL DEFAULT 0.0")

    # Garantir coluna 'estoque' na tabela produtos
    if 'estoque' not in colunas_produtos:
        cursor.execute("ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 0")

    # ── Tabela: estoque_mov ───────────────────────────────────────────
    cursor.execute("PRAGMA table_info(estoque_mov)")
    colunas_estoque = {row['name'] for row in cursor.fetchall()}

    # Adicionar coluna 'motivo' se não existir
    if 'motivo' not in colunas_estoque:
        cursor.execute("ALTER TABLE estoque_mov ADD COLUMN motivo TEXT")

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

# --------------- FUNÇÕES DE NOTA FISCAL (MOD5) ---------------

def criar_nota_fiscal(numero, descricao):
    """Cria uma nova intenção de nota fiscal com status 'rascunho'."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notas_fiscais (numero_nota, descricao, status)
            VALUES (?, ?, 'rascunho')
        ''', (numero, descricao))
        nota_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, nota_id, "Nota criada com sucesso."
    except Exception as e:
        return False, None, str(e)

def listar_notas():
    """Retorna todas as notas fiscais, mais recentes primeiro."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, numero_nota, descricao, status, data_criacao
        FROM notas_fiscais
        ORDER BY data_criacao DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def buscar_nota_por_numero(numero):
    """Retorna uma nota fiscal pelo seu número único."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notas_fiscais WHERE numero_nota = ?', (numero,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def validar_sku_para_nota(nota_id, sku):
    """
    Valida se um SKU pode ser adicionado a uma nota.
    Retorna: (valido: bool, codigo: str, mensagem: str, produto: dict|None)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se a nota está em rascunho
    cursor.execute('SELECT status FROM notas_fiscais WHERE id = ?', (nota_id,))
    nota = cursor.fetchone()
    if nota and nota['status'] != 'rascunho':
        conn.close()
        return False, 'NOTA_EMITIDA', 'Esta nota já foi emitida e não pode ser alterada.', None

    # Verifica se o SKU existe
    cursor.execute('SELECT * FROM produtos WHERE sku = ?', (sku,))
    produto = cursor.fetchone()
    if not produto:
        conn.close()
        return False, 'SKU_INEXISTENTE', f"SKU '{sku}' não encontrado no cadastro de produtos.", None

    # Verifica se o SKU já está na nota
    cursor.execute('SELECT id FROM itens_nota WHERE nota_id = ? AND sku = ?', (nota_id, sku))
    if cursor.fetchone():
        conn.close()
        return False, 'SKU_DUPLICADO', f"SKU '{sku}' já foi adicionado a esta nota.", None

    conn.close()
    return True, 'OK', f"SKU '{sku}' válido: {dict(produto)['nome']}", dict(produto)

def adicionar_item_nota(nota_id, sku, quantidade, preco_base, aliquota):
    """Adiciona um item à nota fiscal e calcula os valores."""
    try:
        valor_bruto   = preco_base * quantidade
        valor_imposto = valor_bruto * aliquota
        valor_total   = valor_bruto + valor_imposto

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO itens_nota
                (nota_id, sku, quantidade, preco_base, aliquota,
                 valor_bruto, valor_imposto, valor_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nota_id, sku, quantidade, preco_base, aliquota,
              valor_bruto, valor_imposto, valor_total))
        conn.commit()
        conn.close()

        valores = {
            'valor_bruto':   round(valor_bruto,   2),
            'valor_imposto': round(valor_imposto, 2),
            'valor_total':   round(valor_total,   2),
        }
        return True, valores, "Item adicionado com sucesso."
    except Exception as e:
        return False, None, str(e)

def listar_itens_nota(nota_id):
    """Retorna todos os itens de uma nota fiscal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.*, p.nome
        FROM itens_nota i
        JOIN produtos p ON i.sku = p.sku
        WHERE i.nota_id = ?
        ORDER BY i.id ASC
    ''', (nota_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def calcular_totais_nota(nota_id):
    """Calcula os totais consolidados de uma nota fiscal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            COUNT(*)        AS num_itens,
            SUM(quantidade) AS total_qtd,
            SUM(valor_bruto)   AS total_bruto,
            SUM(valor_imposto) AS total_imposto,
            SUM(valor_total)   AS total_final
        FROM itens_nota
        WHERE nota_id = ?
    ''', (nota_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row['num_itens']:
        return {
            'num_itens':     row['num_itens'],
            'total_qtd':     row['total_qtd']     or 0,
            'total_bruto':   round(row['total_bruto']   or 0, 2),
            'total_imposto': round(row['total_imposto'] or 0, 2),
            'total_final':   round(row['total_final']   or 0, 2),
        }
    return None

def emitir_nota_fiscal(numero):
    """
    Emite uma nota fiscal: muda status para 'emitida' e
    baixa o estoque de todos os itens da nota.
    Retorna: (sucesso: bool, mensagem: str, relatorio: list[str])
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Busca a nota
        cursor.execute('SELECT * FROM notas_fiscais WHERE numero_nota = ?', (numero,))
        nota = cursor.fetchone()
        if not nota:
            conn.close()
            return False, f"Nota '{numero}' não encontrada.", []

        if nota['status'] == 'emitida':
            conn.close()
            return False, f"A nota '{numero}' já foi emitida.", []

        # 2. Busca os itens
        cursor.execute('''
            SELECT i.sku, i.quantidade, p.nome, p.estoque
            FROM itens_nota i JOIN produtos p ON i.sku = p.sku
            WHERE i.nota_id = ?
        ''', (nota['id'],))
        itens = cursor.fetchall()

        if not itens:
            conn.close()
            return False, "A nota não possui itens. Adicione itens antes de emitir.", []

        # 3. Verifica estoque suficiente para todos os itens
        for item in itens:
            if item['estoque'] < item['quantidade']:
                conn.close()
                return False, (
                    f"Estoque insuficiente para '{item['nome']}' (SKU: {item['sku']}). "
                    f"Disponível: {item['estoque']}, necessário: {item['quantidade']}."
                ), []

        # 4. Baixa o estoque e registra movimentações
        relatorio = []
        for item in itens:
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE sku = ?",
                (item['quantidade'], item['sku'])
            )
            cursor.execute('''
                INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov)
                VALUES (?, 'saida', ?, ?, ?)
            ''', (item['sku'], item['quantidade'],
                  f"Emissão nota {numero}", datetime.now().isoformat()))
            relatorio.append(
                f"  • {item['nome']} (SKU: {item['sku']}): -{item['quantidade']} un."
            )

        # 5. Marca nota como emitida
        cursor.execute(
            "UPDATE notas_fiscais SET status = 'emitida' WHERE id = ?",
            (nota['id'],)
        )
        conn.commit()
        conn.close()
        return True, f"Nota '{numero}' emitida com sucesso!", relatorio

    except Exception as e:
        return False, str(e), []

# --------------- FUNÇÕES DE CAIXA ---------------

def consultar_resumo_caixa():
    """Calcula o Fluxo de Caixa a partir das movimentações de estoque.
    Receitas  = saídas de estoque (vendas)   × preco_base × 1.18
    Despesas  = entradas de estoque (compras) × preco_base
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Receitas: cada venda (saída de estoque) gera receita com imposto embutido
    cursor.execute("""
        SELECT SUM(e.quantidade * p.preco_base * 1.18)
        FROM estoque_mov e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'saida'
    """)
    total_vendas = cursor.fetchone()[0] or 0.0

    # Despesas: cada compra (entrada de estoque) gera custo ao preço base
    cursor.execute("""
        SELECT SUM(e.quantidade * p.preco_base)
        FROM estoque_mov e
        JOIN produtos p ON e.sku = p.sku
        WHERE e.tipo = 'entrada'
    """)
    total_compras = cursor.fetchone()[0] or 0.0

    conn.close()

    return {
        "entradas": round(total_vendas,  2),
        "despesas": round(total_compras, 2),
        "saldo":    round(total_vendas - total_compras, 2)
    }

def registrar_despesa(descricao, valor, data=None):
    """Registra uma despesa no caixa."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if data:
            cursor.execute(
                "INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro) VALUES ('despesa', ?, ?, ?)",
                (descricao, valor, data)
            )
        else:
            cursor.execute(
                "INSERT INTO caixa (tipo, descricao, valor_liquido) VALUES ('despesa', ?, ?)",
                (descricao, valor)
            )

        conn.commit()
        conn.close()
        return True, "Despesa registrada com sucesso."

    except Exception as e:
        return False, str(e)

def consultar_extrato_periodo(data_inicio, data_fim):
    """Retorna todas as transações de caixa em um período."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo, descricao, valor_liquido, data_registro
        FROM caixa
        WHERE date(data_registro) BETWEEN ? AND ?
        ORDER BY data_registro DESC
    """, (data_inicio, data_fim))

    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

def consultar_resumo_financeiro():
    """Retorna resumo financeiro completo com ticket médio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), SUM(valor_liquido) FROM caixa WHERE tipo='entrada'")
    qtd_entradas, total_entradas = cursor.fetchone()
    qtd_entradas   = qtd_entradas   or 0
    total_entradas = total_entradas or 0

    cursor.execute("SELECT COUNT(*), SUM(valor_liquido) FROM caixa WHERE tipo='despesa'")
    qtd_despesas, total_despesas = cursor.fetchone()
    qtd_despesas   = qtd_despesas   or 0
    total_despesas = total_despesas or 0

    saldo = total_entradas - total_despesas

    ticket_entrada = total_entradas / qtd_entradas if qtd_entradas > 0 else 0
    ticket_despesa = total_despesas / qtd_despesas if qtd_despesas > 0 else 0

    conn.close()

    return {
        "total_entradas":        round(total_entradas, 2),
        "total_despesas":        round(total_despesas, 2),
        "saldo":                 round(saldo, 2),
        "qtd_entradas":          qtd_entradas,
        "qtd_despesas":          qtd_despesas,
        "ticket_medio_entrada":  round(ticket_entrada, 2),
        "ticket_medio_despesa":  round(ticket_despesa, 2)
    }
    
def listar_produtos_criticos(limite=5):
    """
    Retorna produtos com estoque igual ou abaixo do limite crítico.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sku, nome, estoque
        FROM produtos
        WHERE estoque <= ?
        ORDER BY estoque ASC, nome ASC
    """, (limite,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
