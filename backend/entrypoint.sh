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
echo "🚀 Starting Flask development server..."
exec flask run --host=0.0.0.0 --port="${PORT:-5000}"
