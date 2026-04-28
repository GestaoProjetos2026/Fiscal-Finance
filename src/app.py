# src/app.py
from flask import Flask
from products  import products_bp
from cashflow  import cashflow_bp
from invoice   import invoice_bp
from auth      import auth_bp, init_db_auth
# IMPORTANTE: Importando o novo módulo de integração
from integration import integration_bp 

app = Flask(__name__)

# ── Registra os módulos com o prefixo /v1/fisc ────────────────
app.register_blueprint(auth_bp,      url_prefix="/v1/fisc")
app.register_blueprint(products_bp, url_prefix="/v1/fisc")
app.register_blueprint(cashflow_bp, url_prefix="/v1/fisc")
app.register_blueprint(invoice_bp,  url_prefix="/v1/fisc")

# TASK: FISC-MOD1-02 e FISC-MOD1-03 — Registra integração externa
app.register_blueprint(integration_bp, url_prefix="/v1/fisc")


if __name__ == "__main__":
    init_db_auth()

    print("=" * 60)
    print("  API Squad FISC  —  http://0.0.0.0:5000")
    print("=" * 60)
    print()
    print("  MOD Auth — Autenticação JWT:")
    print("    POST   /v1/fisc/auth/login")
    print()
    print("  MOD1 — Produtos:")
    print("    GET    /v1/fisc/products")
    print()
    # Adicionando visualização dos novos endpoints no console para facilitar
    print("  MOD Integração — Squads 3 e 4:")
    print("    GET    /v1/fisc/integration/crm/stock/<sku>")
    print("    GET    /v1/fisc/integration/sd/history/<usuario_id>")
    print()
    print("  Pressione CTRL+C para parar.")
    print("=" * 60)

    app.run(debug=False, host="0.0.0.0", port=5000)
