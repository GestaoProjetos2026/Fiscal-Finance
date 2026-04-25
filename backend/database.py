# src/database.py
import sqlite3
import os

# Reutiliza o banco SQLite do protótipo (não precisa criar do zero)
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome (como dicionário)
    return conn
