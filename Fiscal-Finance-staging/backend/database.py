# src/database.py
# Conexão com o banco SQLite compartilhado com o PROTOTIPO
# MOD-S4-02: adicionado init_db() com criação de tabelas + migrações de schema
import sqlite3
import os

# Reutiliza o banco SQLite do protótipo (não precisa criar do zero)
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "PROTOTIPO", "app.db")

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome (como dicionário)
    return conn


def init_db():
    """
    Garante que todas as tabelas existam e que o schema esteja correto.
    Seguro para rodar múltiplas vezes (idempotente).
    Chamado no startup do app.py junto com init_db_auth().
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Tabela: produtos ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            sku               TEXT PRIMARY KEY,
            nome              TEXT NOT NULL,
            preco_base        REAL NOT NULL,
            aliquota_imposto  REAL NOT NULL DEFAULT 0.0,
            estoque           INTEGER DEFAULT 0
        )
    """)

    # ── Tabela: estoque ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            sku                TEXT,
            tipo               TEXT,
            quantidade         INTEGER,
            motivo             TEXT,
            data_movimentacao  TEXT,
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )
    """)

    # ── Tabela: caixa ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixa (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo           TEXT    NOT NULL,
            descricao      TEXT    NOT NULL,
            valor_liquido  REAL    NOT NULL,
            data_registro  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Tabela: notas_fiscais ────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_nota  TEXT    NOT NULL UNIQUE,
            descricao    TEXT    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'rascunho',
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Tabela: itens_nota ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_nota (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nota_id       INTEGER NOT NULL,
            sku           TEXT    NOT NULL,
            quantidade    INTEGER NOT NULL,
            preco_base    REAL    NOT NULL,
            aliquota      REAL    NOT NULL,
            valor_bruto   REAL    NOT NULL,
            valor_imposto REAL    NOT NULL,
            valor_total   REAL    NOT NULL,
            FOREIGN KEY(nota_id) REFERENCES notas_fiscais(id),
            FOREIGN KEY(sku)     REFERENCES produtos(sku)
        )
    """)

    conn.commit()

    # ══ Migrações de schema (idempotentes) ══════════════════════

    # produtos: garante colunas
    cursor.execute("PRAGMA table_info(produtos)")
    cols_prod = {row["name"] for row in cursor.fetchall()}

    if "aliquota_imposto" not in cols_prod:
        try:
            cursor.execute("ALTER TABLE produtos ADD COLUMN aliquota_imposto REAL NOT NULL DEFAULT 0.0")
        except Exception:
            pass

    if "estoque" not in cols_prod:
        try:
            cursor.execute("ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 0")
        except Exception:
            pass

    # estoque: garante coluna 'motivo'
    cursor.execute("PRAGMA table_info(estoque)")
    cols_est = {row["name"] for row in cursor.fetchall()}
    if "motivo" not in cols_est:
        try:
            cursor.execute("ALTER TABLE estoque ADD COLUMN motivo TEXT")
        except Exception:
            pass

    conn.commit()
    conn.close()
