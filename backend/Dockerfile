FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para o psycopg2, utils e postgres-client
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte (será sobrescrito pelo volume em desenvolvimento)
COPY . .

# Dá permissão de execução ao script de inicialização
RUN chmod +x start.sh

EXPOSE 8000

# Comando para rodar a aplicação através do script
CMD ["./start.sh"]
