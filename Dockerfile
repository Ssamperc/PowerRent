FROM python:3.11-slim

# Evitar bytecode y asegurar salida sin buffer (importante para Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema
# - gcc y libpq-dev: requeridos para psycopg2 (cliente PostgreSQL)
# - postgresql-client: para pg_isready en entrypoint.sh
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Crear directorios necesarios para media y static
RUN mkdir -p /app/media /app/static /app/staticfiles

# Hacer ejecutable el script de inicio
RUN chmod +x /app/entrypoint.sh

# Puerto de Django
EXPOSE 8000

# Script de inicio: espera a PostgreSQL, aplica migraciones, luego inicia el servidor
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto: usar runserver en desarrollo, gunicorn en producción
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
