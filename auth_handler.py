import sqlite3
import hashlib
import datetime
import jwt  # Requer: pip install PyJWT

# --- CONFIGURAÇÕES ---
SECRET_KEY = "fiscal_finance_secret_2026"

# =================================================================
# 1. BANCO DE DADOS (Criação da Tabela e Usuário Admin)
# =================================================================

def init_db_auth():
    """
    REQ: Criar tabela de usuários (id, nome, email, senha_hash, papel)
    REQ: Inserir usuário admin
    """
    conn = sqlite3.connect("sistema.db")
    cursor = conn.cursor()
    
    # Criar tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            papel TEXT NOT NULL
        )
    """)
    
    # Gerar Hash da senha 'admin123' e inserir o Admin
    senha_admin_plana = "admin123"
    senha_hash = hashlib.sha256(senha_admin_plana.encode()).hexdigest()
    
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel) 
        VALUES (?, ?, ?, ?)
    """, ("Administrador", "admin@fiscal.com", senha_hash, "admin"))
    
    conn.commit()
    conn.close()
    print("Banco de dados de autenticação inicializado.")

# =================================================================
# 2. LÓGICA DE JWT E SEGURANÇA (Middleware)
# =================================================================

def gerar_jwt(usuario_id, papel):
    """
    REQ: Implementar JWT com expiração
    """
    payload = {
        "id": usuario_id,
        "papel": papel,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def middleware_protecao(auth_header):
    """
    REQ: Criar middleware de proteção (Ler header Authorization: Bearer TOKEN)
    REQ: Bloquear se inválido
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload  # Token válido
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None  # Token inválido ou expirado

# =================================================================
# 3. ENDPOINTS (Lógica Prática)
# =================================================================

def endpoint_login(email, senha_plana):
    """
    REQ: Rota: POST /auth/login
    Valida no banco e Gera JWT
    """
    senha_hash_tentativa = hashlib.sha256(senha_plana.encode()).hexdigest()
    
    conn = sqlite3.connect("sistema.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?", 
                   (email, senha_hash_tentativa))
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        token = gerar_jwt(usuario['id'], usuario['papel'])
        return {"status": "success", "token": f"Bearer {token}"}
    else:
        return {"status": "error", "message": "Acesso Negado"}

def endpoint_me(auth_header):
    """
    REQ: Rota /auth/me -> retorna usuário logado
    """
    usuario_dados = middleware_protecao(auth_header)
    if usuario_dados:
        return {"status": "success", "user_id": usuario_dados['id'], "papel": usuario_dados['papel']}
    return {"status": "error", "message": "Não autorizado"}

def endpoint_logout():
    """
    REQ: Rota /auth/logout -> invalidar token
    Nota: Em JWT (stateless), o logout é feito limpando o token no cliente.
    """
    return {"status": "success", "message": "Logout realizado com sucesso"}

# =================================================================
# EXEMPLO DE TESTE (Pode apagar essa parte ao integrar)
# =================================================================
if __name__ == "__main__":
    init_db_auth() # Inicializa banco
    
    # 1. Testando Login
    print("\n--- Tentando Login ---")
    resposta_login = endpoint_login("admin@fiscal.com", "admin123")
    print(resposta_login)
    
    if resposta_login["status"] == "success":
        token_recebido = resposta_login["token"]
        
        # 2. Testando Rota Protegida (/me)
        print("\n--- Acessando /auth/me com Token ---")
        print(endpoint_me(token_recebido))
        
        # 3. Testando Acesso com Token Falso
        print("\n--- Testando Acesso Negado ---")
        print(endpoint_me("Bearer TOKEN_FALSO"))
