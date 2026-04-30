# src/auth.py
# FISC-MOD2 Sprint 2 — Autenticação JWT
# Adaptado de auth_handler.py (feat/auth-security) por kaua-silva09
# Integrado como Flask Blueprint por Kevin para src/
#
# FISC-12: POST /v1/fisc/auth/login
# FISC-13: Middleware JWT (middleware_jwt)
# FISC-14: Tabela usuarios + seed admin
# FISC-15: GET  /v1/fisc/auth/me  |  POST /v1/fisc/auth/logout
#
# MOD-S4-02 (RBAC):
# FISC-MOD2-01: RBAC em produtos
# FISC-MOD2-02: RBAC em estoque
# FISC-MOD2-03: RBAC em fiscal
# FISC-MOD2-04: RBAC em caixa
# FISC-MOD2-05: Tela de gestão de usuários (endpoints)

import hashlib
import datetime
from flask import Blueprint, request, jsonify, g
import jwt

from database import get_connection

auth_bp = Blueprint("auth", __name__)

# ── Configuração ────────────────────────────────────────────────
# ⚠️  Em produção, mova para variável de ambiente (os.environ)
SECRET_KEY = "fiscal_finance_squad_2026_secret"   # >= 32 bytes para HS256


# ── Papéis disponíveis (MOD-S4-02) ─────────────────────────────
# Hierarquia: admin > gerente > operador
PAPEIS_VALIDOS = ("admin", "gerente", "operador")

# Mapa de permissões por papel para cada módulo
PERMISSOES = {
    # produtos
    "produtos.ler":    {"admin", "gerente", "operador"},
    "produtos.criar":  {"admin", "gerente"},
    "produtos.editar": {"admin", "gerente"},
    "produtos.deletar":{"admin"},
    # estoque
    "estoque.ler":     {"admin", "gerente", "operador"},
    "estoque.entrada": {"admin", "gerente"},
    "estoque.saida":   {"admin", "gerente"},
    # fiscal (notas)
    "fiscal.intent":   {"admin", "gerente", "operador"},
    "fiscal.confirm":  {"admin", "gerente"},
    "fiscal.ler":      {"admin", "gerente", "operador"},
    # caixa
    "caixa.ler":       {"admin", "gerente", "operador"},
    "caixa.despesa":   {"admin", "gerente"},
    # usuarios
    "usuarios.ler":    {"admin"},
    "usuarios.criar":  {"admin"},
    "usuarios.editar": {"admin"},
    "usuarios.deletar":{"admin"},
}


# ── Inicialização da tabela de usuários (FISC-14 + MOD-S4-02) ───
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
            papel      TEXT    NOT NULL DEFAULT 'operador',
            ativo      INTEGER NOT NULL DEFAULT 1,
            criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração: adiciona coluna 'ativo' se não existir (bancos antigos)
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
    except Exception:
        pass

    # Migração: converte papel legado 'usuario' para 'operador' (MOD-S4-02)
    cursor.execute("UPDATE usuarios SET papel = 'operador' WHERE papel = 'usuario'")

    # Seed: admin inicial
    senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel, ativo)
        VALUES (?, ?, ?, ?, 1)
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


def requer_papel(*permissoes):
    """
    Decorator RBAC (MOD-S4-02) — exige autenticação JWT e verifica se o
    papel do usuário possui todas as permissões listadas.

    Uso:
        @requer_papel("produtos.criar")
        def criar_produto(): ...
    """
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            payload = validar_token(request.headers.get("Authorization", ""))
            if not payload:
                return jsonify({
                    "status": "error", "data": None,
                    "message": "Não autorizado. Faça login e use o header Authorization: Bearer <token>."
                }), 401

            papel_usuario = payload.get("papel", "")

            # Papel legado ou inválido (ex: 'usuario' antes do RBAC) → força re-login
            if papel_usuario not in PAPEIS_VALIDOS:
                return jsonify({
                    "status": "error", "data": None,
                    "message": "Sessão desatualizada. Faça login novamente para atualizar suas permissões."
                }), 401

            for perm in permissoes:
                permitidos = PERMISSOES.get(perm, set())
                if papel_usuario not in permitidos:
                    return jsonify({
                        "status": "error", "data": None,
                        "message": f"Acesso negado. Permissão necessária: '{perm}'. Seu papel: '{papel_usuario}'."
                    }), 403

            g.usuario = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator


def tem_permissao(papel: str, permissao: str) -> bool:
    """Verifica se um papel possui determinada permissão."""
    return papel in PERMISSOES.get(permissao, set())


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
        "SELECT id, nome, papel, ativo FROM usuarios WHERE email = ? AND senha_hash = ?",
        (email, senha_hash)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return jsonify({"status": "error", "data": None,
                        "message": "Credenciais inválidas."}), 401

    u = dict(usuario)

    # Bloqueia usuários desativados (MOD-S4-02)
    if not u.get("ativo", 1):
        return jsonify({"status": "error", "data": None,
                        "message": "Conta desativada. Contate o administrador."}), 403

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


# ════════════════════════════════════════════════════════════════
# FISC-MOD2-05 — Gestão de Usuários (admin only)
# ════════════════════════════════════════════════════════════════

# ── GET /auth/users ─────────────────────────────────────────────
@auth_bp.route("/auth/users", methods=["GET"])
@requer_papel("usuarios.ler")
def listar_usuarios():
    """
    Lista todos os usuários cadastrados.
    Requer papel: admin.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, papel, ativo, criado_em FROM usuarios ORDER BY id")
    usuarios = [dict(u) for u in cursor.fetchall()]
    conn.close()

    return jsonify({
        "status": "success",
        "data": usuarios,
        "message": f"{len(usuarios)} usuário(s) encontrado(s)."
    }), 200


# ── POST /auth/users ─────────────────────────────────────────────
@auth_bp.route("/auth/users", methods=["POST"])
@requer_papel("usuarios.criar")
def criar_usuario():
    """
    Cria um novo usuário.
    Requer papel: admin.
    Body: { "nome": "João", "email": "joao@email.com", "senha": "123456", "papel": "operador" }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo da requisição inválido."}), 400

    nome   = str(dados.get("nome",  "")).strip()
    email  = str(dados.get("email", "")).strip().lower()
    senha  = str(dados.get("senha", ""))
    papel  = str(dados.get("papel", "operador")).strip().lower()

    if not nome:
        return jsonify({"status": "error", "data": None, "message": "Campo 'nome' é obrigatório."}), 400
    if not email:
        return jsonify({"status": "error", "data": None, "message": "Campo 'email' é obrigatório."}), 400
    if not senha or len(senha) < 6:
        return jsonify({"status": "error", "data": None, "message": "Campo 'senha' deve ter ao menos 6 caracteres."}), 400
    if papel not in PAPEIS_VALIDOS:
        return jsonify({"status": "error", "data": None,
                        "message": f"Papel inválido. Use: {', '.join(PAPEIS_VALIDOS)}."}), 400

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES (?, ?, ?, ?, 1)",
            (nome, email, senha_hash, papel)
        )
        conn.commit()
        novo_id = cursor.lastrowid
    except Exception:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"E-mail '{email}' já está cadastrado."}), 409
    conn.close()

    return jsonify({
        "status": "success",
        "data": {"id": novo_id, "nome": nome, "email": email, "papel": papel, "ativo": 1},
        "message": "Usuário criado com sucesso."
    }), 201


# ── PUT /auth/users/<id> ─────────────────────────────────────────
@auth_bp.route("/auth/users/<int:usuario_id>", methods=["PUT"])
@requer_papel("usuarios.editar")
def editar_usuario(usuario_id):
    """
    Atualiza nome, papel e/ou senha de um usuário.
    Requer papel: admin.
    Body (campos opcionais): { "nome": "...", "papel": "gerente", "senha": "nova123" }
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Corpo da requisição inválido."}), 400

    # Impede que o admin edite seu próprio papel (para não se auto-rebaixar)
    if usuario_id == g.usuario["id"] and "papel" in dados:
        return jsonify({"status": "error", "data": None,
                        "message": "Você não pode alterar seu próprio papel."}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": "Usuário não encontrado."}), 404

    u = dict(usuario)
    novo_nome  = str(dados.get("nome",  u["nome"])).strip() or u["nome"]
    novo_papel = str(dados.get("papel", u["papel"])).strip().lower()
    novo_ativo = dados.get("ativo", u.get("ativo", 1))
    nova_senha_hash = u["senha_hash"]

    if novo_papel not in PAPEIS_VALIDOS:
        conn.close()
        return jsonify({"status": "error", "data": None,
                        "message": f"Papel inválido. Use: {', '.join(PAPEIS_VALIDOS)}."}), 400

    nova_senha = dados.get("senha")
    if nova_senha:
        if len(nova_senha) < 6:
            conn.close()
            return jsonify({"status": "error", "data": None,
                            "message": "Nova senha deve ter ao menos 6 caracteres."}), 400
        nova_senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()

    cursor.execute(
        "UPDATE usuarios SET nome = ?, papel = ?, ativo = ?, senha_hash = ? WHERE id = ?",
        (novo_nome, novo_papel, int(novo_ativo), nova_senha_hash, usuario_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "data": {"id": usuario_id, "nome": novo_nome, "papel": novo_papel, "ativo": int(novo_ativo)},
        "message": "Usuário atualizado com sucesso."
    }), 200


# ── DELETE /auth/users/<id> ──────────────────────────────────────
@auth_bp.route("/auth/users/<int:usuario_id>", methods=["DELETE"])
@requer_papel("usuarios.deletar")
def desativar_usuario(usuario_id):
    """
    Desativa (soft-delete) um usuário — não apaga do banco.
    Requer papel: admin.
    """
    if usuario_id == g.usuario["id"]:
        return jsonify({"status": "error", "data": None,
                        "message": "Você não pode desativar sua própria conta."}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": "Usuário não encontrado."}), 404

    cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "data": None,
        "message": f"Usuário '{dict(usuario)['nome']}' desativado com sucesso."
    }), 200


# ── GET /auth/permissions ────────────────────────────────────────
@auth_bp.route("/auth/permissions", methods=["GET"])
@requer_auth
def listar_permissoes():
    """
    Retorna o mapa completo de permissões do sistema (RBAC).
    Qualquer usuário autenticado pode consultar.
    """
    mapa = {perm: sorted(papeis) for perm, papeis in PERMISSOES.items()}
    papel_atual = g.usuario.get("papel", "")
    minhas_permissoes = [p for p, s in PERMISSOES.items() if papel_atual in s]

    return jsonify({
        "status": "success",
        "data": {
            "papeis_validos": list(PAPEIS_VALIDOS),
            "mapa_permissoes": mapa,
            "meu_papel": papel_atual,
            "minhas_permissoes": sorted(minhas_permissoes)
        },
        "message": "Mapa de permissões RBAC."
    }), 200
