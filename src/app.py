# src/app.py
# Ponto de entrada da API REST — Squad FISC
# Para rodar: python app.py (dentro da pasta src/)

import json
import os
from flask import Flask, jsonify
from flasgger import Swagger

from products   import products_bp
from cashflow   import cashflow_bp
from invoice    import invoice_bp
from auth       import auth_bp, init_db_auth
from public_api import public_bp

app = Flask(__name__)

# ── Swagger UI — acessível em GET /docs ───────────────────────
_SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.json")

with open(_SPEC_PATH, encoding="utf-8") as f:
    _openapi_spec = json.load(f)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route":    "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
}

Swagger(app, config=swagger_config, template=_openapi_spec)


# ── Registra os módulos com o prefixo /v1/fisc ────────────────
app.register_blueprint(auth_bp,     url_prefix="/v1/fisc")
app.register_blueprint(products_bp, url_prefix="/v1/fisc")
app.register_blueprint(cashflow_bp, url_prefix="/v1/fisc")
app.register_blueprint(invoice_bp,  url_prefix="/v1/fisc")
app.register_blueprint(public_bp,   url_prefix="/v1")      # prefixo /v1 (public já inclui /public/fisc)


# ── Handler global de erros ───────────────────────────────────
@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({"status": "error", "data": None, "message": "Rota não encontrada."}), 404

@app.errorhandler(405)
def metodo_nao_permitido(e):
    return jsonify({"status": "error", "data": None, "message": "Método HTTP não permitido."}), 405

@app.errorhandler(500)
def erro_interno(e):
    return jsonify({"status": "error", "data": None, "message": "Erro interno do servidor."}), 500


if __name__ == "__main__":
    init_db_auth()  # garante tabela usuarios + seed admin

    print("=" * 65)
    print("  API Squad FISC  —  http://0.0.0.0:5000")
    print("=" * 65)
    print()
    print("  Auth:")
    print("   POST   /v1/fisc/auth/login")
    print("   GET    /v1/fisc/auth/me           [requer JWT]")
    print("   POST   /v1/fisc/auth/logout       [requer JWT]")
    print()
    print("  Produtos:")
    print("   POST   /v1/fisc/products")
    print("   GET    /v1/fisc/products[?nome=]")
    print("   GET    /v1/fisc/products/<sku>")
    print("   PUT    /v1/fisc/products/<sku>")
    print("   DELETE /v1/fisc/products/<sku>")
    print()
    print("  Nota Fiscal:")
    print("   POST   /v1/fisc/invoice/intent")
    print("   POST   /v1/fisc/invoice/confirm")
    print("   GET    /v1/fisc/invoice/<numero>")
    print()
    print("  Caixa:")
    print("   GET    /v1/fisc/cashflow/balance")
    print("   POST   /v1/fisc/cashflow/expense")
    print("   GET    /v1/fisc/cashflow/statement?from=&to=")
    print()
    print("  API Pública (X-API-KEY):")
    print("   GET    /v1/public/fisc/products/<sku>")
    print("   GET    /v1/public/fisc/stock/<sku>")
    print("   GET    /v1/public/fisc/cashflow/summary")
    print()
    print("  Swagger UI (documentação interativa):")
    print("   GET    http://0.0.0.0:5000/docs")
    print()
    print("  Pressione CTRL+C para parar.")
    print("=" * 65)

    app.run(debug=False, host="0.0.0.0", port=5000)
