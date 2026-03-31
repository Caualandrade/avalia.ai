#!/bin/bash

# Espera o banco de dados estar pronto
echo "Aguardando Banco de Dados no host 'db'..."
until pg_isready -h db -U user -d maturidade_ti; do
  echo "Banco de dados ainda indisponível. Re-tentando em 3s..."
  sleep 3
done
echo "Banco de dados disponível!"

# Executa migrações (se houver)
echo "Executando migrações e seed..."
python migrate.py
python seed.py

# Inicia a aplicação
echo "Iniciando Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
