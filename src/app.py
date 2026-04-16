# src/app.py
# Ponto de entrada da API REST do Squad FISC
# Para rodar: python app.py (dentro da pasta src/)
from flask import Flask
from products import products_bp

app = Flask(__name__)

# Registra as rotas de produtos com o prefixo /v1/fisc
# Resultado: /v1/fisc/products, /v1/fisc/products/<sku>, etc.
app.register_blueprint(products_bp, url_prefix="/v1/fisc")


if __name__ == "__main__":
    print("=" * 50)
    print("API Squad FISC rodando em http://localhost:5000")
    print("=" * 50)
    print("")
    print("   Endpoints de Produtos disponiveis:")
    print("   POST   http://localhost:5000/v1/fisc/products")
    print("   GET    http://localhost:5000/v1/fisc/products")
    print("   GET    http://localhost:5000/v1/fisc/products/<sku>")
    print("   PUT    http://localhost:5000/v1/fisc/products/<sku>")
    print("   DELETE http://localhost:5000/v1/fisc/products/<sku>")
    print("")
    print("   Pressione CTRL+C para parar o servidor.")
    print("=" * 50)
    app.run(debug=True, port=5000)
