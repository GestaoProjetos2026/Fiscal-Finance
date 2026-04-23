# src/auth.py
# FISC-MOD2 Sprint 2 — Autenticação JWT
# Adaptado de auth_handler.py (feat/auth-security) por kaua-silva09
# Integrado como Flask Blueprint por Kevin para src/
#
# FISC-12: POST /v1/fisc/auth/login
# FISC-13: Middleware JWT (middleware_jwt)
# FISC-14: Tabela usuarios + seed admin
# FISC-15: GET  /v1/fisc/auth/me  |  POST /v1/fisc/auth/logout

import hashlib
import datetime
from flask import Blueprint, request, jsonify, g
import jwt

from database import get_connection

auth_bp = Blueprint("auth", __name__)

# ── Configuração ────────────────────────────────────────────────
# ⚠️  Em produção, mova para variável de ambiente (os.environ)
SECRET_KEY = "fiscal_finance_squad_2026_secret"   # >= 32 bytes para HS256


# ── Inicialização da tabela de usuários (FISC-14) ───────────────
def init_db_auth():
    """Cria a tabela 'usuarios' e insere o admin padrão se não existir."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            senha_hash TEXT    NOT NULL,
            papel      TEXT    NOT NULL DEFAULT 'usuario',
            criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed: admin inicial
    senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
        VALUES (?, ?, ?, ?)
    """, ("Administrador", "admin@fiscal.com", senha_hash, "admin"))

    conn.commit()
    conn.close()


# ── Helpers JWT (FISC-13) ────────────────────────────────────────
def gerar_token(usuario_id: int, papel: str) -> str:
    payload = {
        "id":    usuario_id,
        "papel": papel,
        "exp":   datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def validar_token(auth_header: str):
    """Retorna o payload decodificado ou None se inválido/expirado."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def requer_auth(f):
    """Decorator — protege qualquer rota com JWT."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        payload = validar_token(request.headers.get("Authorization", ""))
        if not payload:
            return jsonify({
                "status": "error", "data": None,
                "message": "Não autorizado. Faça login e use o header Authorization: Bearer <token>."
            }), 401
        g.usuario = payload   # disponível para a rota
        return f(*args, **kwargs)
    return wrapper


# ── FISC-12 — POST /auth/login ───────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Realiza o login e retorna um token JWT.
    Body: { "email": "admin@fiscal.com", "senha": "admin123" }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo da requisição inválido."}), 400

    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))

    if not email or not senha:
        return jsonify({"status": "error", "data": None,
                        "message": "Campos 'email' e 'senha' são obrigatórios."}), 400

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, papel FROM usuarios WHERE email = ? AND senha_hash = ?",
        (email, senha_hash)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return jsonify({"status": "error", "data": None,
                        "message": "Credenciais inválidas."}), 401

    u = dict(usuario)
    token = gerar_token(u["id"], u["papel"])

    return jsonify({
        "status": "success",
        "data": {
            "token":  f"Bearer {token}",
            "id":     u["id"],
            "nome":   u["nome"],
            "papel":  u["papel"],
            "expira": "24h"
        },
        "message": "Login realizado com sucesso."
    }), 200


# ── FISC-15a — GET /auth/me ──────────────────────────────────────
@auth_bp.route("/auth/me", methods=["GET"])
@requer_auth
def me():
    """Retorna os dados do usuário logado a partir do token JWT."""
    payload = g.usuario

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, email, papel, criado_em FROM usuarios WHERE id = ?",
        (payload["id"],)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return jsonify({"status": "error", "data": None,
                        "message": "Usuário não encontrado."}), 404

    return jsonify({
        "status": "success",
        "data":    dict(usuario),
        "message": "Dados do usuário logado."
    }), 200


# ── FISC-15b — POST /auth/logout ────────────────────────────────
@auth_bp.route("/auth/logout", methods=["POST"])
@requer_auth
def logout():
    """
    Logout stateless: JWT não tem invalidação server-side.
    O cliente deve descartar o token localmente.
    """
    return jsonify({
        "status":  "success",
        "data":    None,
        "message": "Logout realizado. Descarte o token no cliente."
    }), 200
