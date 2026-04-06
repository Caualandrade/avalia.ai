#!/bin/bash

# Verifica e aguarda banco de dados (compatível com host remoto e local)
if [ -n "$DATABASE_URL" ]; then
  # Extrai host da DATABASE_URL
  DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:/]+).*/\1/')
  echo "Aguardando Banco de Dados em '$DB_HOST'..."
  
  # Tenta conectar por até 30 segundos
  for i in {1..30}; do
    if PGPASSWORD=$(echo $DATABASE_URL | sed -E 's/.*:([^@]+)@.*/\1/') \
       pg_isready -h "$DB_HOST" -U $(echo $DATABASE_URL | sed -E 's/.*\/\//([^:]+).*/\1/') 2>/dev/null; then
      echo "Banco de dados disponível!"
      break
    fi
    echo "Tentativa $i/30: Banco indisponível. Re-tentando em 1s..."
    sleep 1
  done
fi

# Executa migrações (se houver)
echo "Executando migrações e seed..."
python migrate.py || true
python seed.py || true

# Inicia a aplicação
echo "Iniciando Uvicorn em porta $PORT (padrão: 8000)"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
