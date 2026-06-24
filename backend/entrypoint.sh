#!/bin/sh
# entrypoint.sh — runs inside the backend container on startup
set -e

echo "============================================"
echo "  Finanzas IA WhatsApp — Backend Starting"
echo "============================================"

echo ""
echo "⏳ Running database migrations..."
flask db upgrade
echo "✅ Migrations applied."

echo ""
echo "🌱 Seeding initial data..."
flask seed-db
echo "✅ Seed complete."

echo ""
echo "🚀 Starting server..."
if [ "$FLASK_ENV" = "production" ]; then
    echo "Running in PRODUCTION mode with gunicorn"
    exec gunicorn --bind 0.0.0.0:"${PORT:-5000}" --workers 2 --timeout 120 "run:app"
else
    echo "Running in DEVELOPMENT mode with flask run"
    exec flask run --host=0.0.0.0 --port="${PORT:-5000}"
fi
