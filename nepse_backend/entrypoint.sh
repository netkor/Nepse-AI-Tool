#!/bin/bash
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
retries=30
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
s.connect(('${POSTGRES_HOST:-postgres}', ${POSTGRES_PORT:-5432}))
s.close()
" 2>/dev/null; do
    retries=$((retries - 1))
    if [ $retries -le 0 ]; then
        echo "ERROR: database connection failure - host=${POSTGRES_HOST:-postgres} port=${POSTGRES_PORT:-5432}"
        exit 1
    fi
    sleep 1
done

echo "PostgreSQL is ready."

# Run migrations
python manage.py migrate --noinput

# Execute the main command
exec "$@"
