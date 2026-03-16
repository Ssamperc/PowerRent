#!/bin/bash

# entrypoint.sh — Script de inicio para el contenedor Django de PowerRent
# Se ejecuta automáticamente cuando Docker Compose levanta el contenedor web.

set -e

echo ""
echo "=========================================="
echo "  PowerRent — Iniciando contenedor"
echo "=========================================="

# Esperar a que PostgreSQL esté disponible antes de continuar
echo "⏳ Esperando a que PostgreSQL esté disponible..."
while ! pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -q; do
    echo "   PostgreSQL no está listo aún, esperando 2 segundos..."
    sleep 2
done
echo "✅ PostgreSQL está listo en $DB_HOST:${DB_PORT:-5432}"

# Generar migraciones para todos los modelos personalizados
echo ""
echo "🔄 Generando migraciones..."
python manage.py makemigrations usuarios equipos reservas pagos core --noinput 2>/dev/null || true

# Aplicar todas las migraciones (Django built-in + apps personalizadas)
echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos para WhiteNoise
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput

echo ""
echo "✅ Iniciando servidor Django..."
echo "   → http://localhost:8000/"
echo "   → http://localhost:8000/admin/"
echo "   → http://localhost:8000/dashboard/"
echo ""

# Ejecutar el comando pasado como argumento (ej: runserver o gunicorn)
exec "$@"
