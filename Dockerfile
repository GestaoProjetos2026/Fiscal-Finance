FROM python:3.10-slim

WORKDIR /app

# Copia os requisitos e instala
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto (backend, frontend, data, etc.)
COPY . .

# A aplicação Flask roda dentro da pasta backend
WORKDIR /app/backend

# Expor a porta que o Flask utiliza
EXPOSE 5000

# Executa a API
CMD ["python", "app.py"]
