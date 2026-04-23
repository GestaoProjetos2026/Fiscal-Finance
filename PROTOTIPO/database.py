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

def emitir_nota_fiscal(numero_nota):
    """
    Emite a nota fiscal de forma atômica:
      1. Valida que a nota existe e está em 'rascunho'
      2. Valida que a nota possui pelo menos um item
      3. Verifica saldo de estoque suficiente para TODOS os itens
      4. Registra baixa ('saida') no estoque para cada item
      5. Muda o status da nota para 'emitida'
    Se qualquer etapa falhar, faz rollback e nenhuma alteração é salva.
    Retorna (sucesso: bool, mensagem: str, relatorio: list | None)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Etapa 1: nota existe e está em rascunho?
        cursor.execute("SELECT id, status FROM notas_fiscais WHERE numero_nota=?", (numero_nota,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, f"Nota '{numero_nota}' não encontrada.", None
        nota_id, status = row
        if status != 'rascunho':
            conn.close()
            return False, f"A nota '{numero_nota}' já foi emitida anteriormente.", None

        # Etapa 2: nota possui itens?
        cursor.execute("SELECT sku, quantidade FROM itens_nota WHERE nota_id=?", (nota_id,))
        itens = cursor.fetchall()
        if not itens:
            conn.close()
            return False, "A nota não possui itens. Adicione pelo menos um item antes de emitir.", None

        # Etapa 3: verificar saldo de estoque para cada item
        sem_estoque = []
        for sku, quantidade in itens:
            cursor.execute("SELECT SUM(quantidade) FROM estoque WHERE sku=? AND tipo='entrada'", (sku,))
            entradas = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(quantidade) FROM estoque WHERE sku=? AND tipo='saida'", (sku,))
            saidas = cursor.fetchone()[0] or 0
            saldo = entradas - saidas
            if saldo < quantidade:
                sem_estoque.append(f"  SKU {sku}: saldo disponível = {saldo} | necessário = {quantidade}")
        if sem_estoque:
            conn.close()
            return False, "Estoque insuficiente para os seguintes itens:\n" + "\n".join(sem_estoque), None

        # Etapa 4: registrar baixa de estoque para cada item
        relatorio = []
        for sku, quantidade in itens:
            cursor.execute(
                "INSERT INTO estoque (sku, tipo, quantidade) VALUES (?, 'saida', ?)",
                (sku, quantidade)
            )
            relatorio.append(f"  ✅ Baixa: SKU {sku} — {quantidade} unidade(s)")

        # Etapa 5: mudar status para 'emitida'
        cursor.execute("UPDATE notas_fiscais SET status='emitida' WHERE id=?", (nota_id,))

        conn.commit()
        conn.close()
        return True, f"Nota '{numero_nota}' emitida com sucesso!", relatorio

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Erro ao emitir nota: {str(e)}", None
