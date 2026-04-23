# api.py
from flask import Flask
from stock import stock_bp
import database # Importa para que as tabelas sejam inicializadas (e as migrações rodem)

# Se existisse o products.py importaríamos, mas como não tem, mantemos só o stock
# from products import products_bp

# Garante que o DB seja inicializado corretamente
database.init_db()

app = Flask(__name__)

# app.register_blueprint(products_bp, url_prefix="/v1/fisc")
app.register_blueprint(stock_bp, url_prefix="/v1/fisc")

if __name__ == "__main__":
    print("Iniciando a API web (Flask) do Módulo de Estoque!")
    print("Acesse em: http://localhost:5000/v1/fisc/stock/PROD-001")
    app.run(host="0.0.0.0", port=5000, debug=True)
