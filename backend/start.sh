#!/bin/bash

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
  DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:/]+).*/\1/')
  echo "Waiting for Database at '$DB_HOST'..."
  
  for i in {1..30}; do
    if pg_isready -h "$DB_HOST" -U $(echo $DATABASE_URL | sed -E 's/.*\/\//([^:]+).*/\1/') 2>/dev/null; then
      echo "Database is available!"
      break
    fi
    echo "Database unavailable. Attempt $i/30. Retrying in 1s..."
    sleep 1
  done
fi

# Run migrations
echo "Running migrations and seed..."
python migrate.py || true
python seed.py || true

# Start application
echo "Starting Uvicorn on port $PORT (default: 8000)"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
