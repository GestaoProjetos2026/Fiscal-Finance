# src/app.py
# Ponto de entrada da API REST — Squad FISC
# Para rodar: python app.py (dentro da pasta src/)

from flask import Flask
from products  import products_bp
from cashflow  import cashflow_bp
from invoice   import invoice_bp
from auth      import auth_bp, init_db_auth

app = Flask(__name__)

# ── Registra os módulos com o prefixo /v1/fisc ────────────────
app.register_blueprint(auth_bp,     url_prefix="/v1/fisc")
app.register_blueprint(products_bp, url_prefix="/v1/fisc")
app.register_blueprint(cashflow_bp, url_prefix="/v1/fisc")
app.register_blueprint(invoice_bp,  url_prefix="/v1/fisc")


if __name__ == "__main__":
    # Garante que a tabela de usuários existe antes de iniciar
    init_db_auth()

    print("=" * 60)
    print("  API Squad FISC  —  http://0.0.0.0:5000")
    print("=" * 60)
    print()
    print("  MOD Auth — Autenticação JWT:")
    print("   POST   /v1/fisc/auth/login")
    print("   GET    /v1/fisc/auth/me           [requer token]")
    print("   POST   /v1/fisc/auth/logout       [requer token]")
    print()
    print("  MOD1 — Produtos:")
    print("   POST   /v1/fisc/products")
    print("   GET    /v1/fisc/products")
    print("   GET    /v1/fisc/products/<sku>")
    print("   PUT    /v1/fisc/products/<sku>")
    print("   DELETE /v1/fisc/products/<sku>")
    print()
    print("  MOD5 — Nota Fiscal:")
    print("   POST   /v1/fisc/invoice/intent")
    print("   POST   /v1/fisc/invoice/confirm")
    print("   GET    /v1/fisc/invoice/<numero>")
    print()
    print("  MOD4 — Fluxo de Caixa:")
    print("   GET    /v1/fisc/cashflow/balance")
    print("   POST   /v1/fisc/cashflow/expense")
    print("   GET    /v1/fisc/cashflow/statement?from=YYYY-MM-DD&to=YYYY-MM-DD")
    print()
    print("  Pressione CTRL+C para parar.")
    print("=" * 60)

    # host="0.0.0.0" permite acesso externo quando no servidor do prof
    app.run(debug=False, host="0.0.0.0", port=5000)
