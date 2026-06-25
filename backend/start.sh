#!/bin/bash
set -e

# Wait for PostgreSQL database using standard Python socket library
python -c "
import socket
import time
import urllib.parse
import os
import sys

db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print('DATABASE_URL environment variable is missing!')
    sys.exit(1)

# Handle different database URL schemes
parsed = urllib.parse.urlparse(db_url)
netloc = parsed.netloc
if '@' in netloc:
    netloc = netloc.split('@')[1]
if ':' in netloc:
    host, port = netloc.split(':')
    port = int(port)
else:
    host, port = netloc, 5432

print(f'Connecting to database host: {host}:{port}...')
retries = 30
while retries > 0:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        print('Database connection established successfully!')
        break
    except socket.error as e:
        print(f'Database not ready yet ({e}). Waiting 1s... ({retries} retries left)')
        time.sleep(1)
        retries -= 1
"

# Run Alembic Database Migrations
print("Running Alembic DB migrations...")
alembic upgrade head
print("Migrations completed successfully.")

# Start Uvicorn ASGI Application with optimized parameters
# In Cloud Run or production, bind port to $PORT (usually 8080)
PORT_NUM=${PORT:-8080}
echo "Starting application server on port $PORT_NUM..."

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT_NUM" --workers 4 --proxy-headers --forwarded-allow-ips="*"
