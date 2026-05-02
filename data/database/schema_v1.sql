-- =============================================================
-- Squad FISC — Schema v1.0 (SQLite — Protótipo Desktop)
-- Sprint 1 · FISC-03, FISC-04, FISC-05
-- =============================================================
-- NOTA: Este schema é para o protótipo desktop (SQLite).
-- A versão de produção (MySQL/PostgreSQL) será criada no Sprint 2
-- como schema_v2_mysql.sql (FISC-10).
-- =============================================================

-- Tabela 1: Produtos (MOD1)
CREATE TABLE IF NOT EXISTS produtos (
    sku               TEXT PRIMARY KEY,
    nome              TEXT NOT NULL,
    preco_base        REAL NOT NULL,
    aliquota_imposto  REAL NOT NULL  -- valor decimal: ex. 0.12 = 12%
);

-- Tabela 2: Estoque — Histórico de Movimentações (MOD2)
CREATE TABLE IF NOT EXISTS estoque (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    sku                TEXT NOT NULL,
    tipo               TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
    quantidade         INTEGER NOT NULL CHECK(quantidade > 0),
    data_movimentacao  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sku) REFERENCES produtos(sku)
);

-- Tabela 3: Caixa — Fluxo Financeiro (MOD4)
-- (MOD3 - Notas Fiscais será expandido no Sprint 2 com tabelas notas/itens_nota)
CREATE TABLE IF NOT EXISTS caixa (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK(tipo IN ('entrada', 'despesa')),
    descricao       TEXT NOT NULL,
    valor_liquido   REAL NOT NULL CHECK(valor_liquido > 0),
    data_registro   DATETIME DEFAULT CURRENT_TIMESTAMP
);
