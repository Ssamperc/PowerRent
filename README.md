# PowerRent - Sistema de Alquiler de Equipos

Sistema web para alquiler de equipos de construcción desarrollado con **Python + Django** y **Docker**.

## Descripción

PowerRent es una plataforma de alquiler de equipos de construcción y herramientas profesionales. El sistema permite a clientes buscar, reservar y pagar el alquiler de equipos, mientras que los administradores gestionan el inventario, confirman reservas y controlan pagos.

**Tipo de equipos**: Herramientas eléctricas, equipos de compactación, mezcladoras, andamios, cortadoras y motobombas para el sector de la construcción.

**Público objetivo**: Contratistas, constructoras y personas naturales que realizan obras de construcción o remodelación.

**Diferenciador**: Reserva instantánea online con confirmación automática, sin necesidad de llamadas telefónicas.

## Stack Tecnológico

- **Backend**: Python 3.11 + Django 4.2
- **Base de datos**: PostgreSQL 15
- **Contenedores**: Docker + Docker Compose
- **Frontend**: Bootstrap 5 + Django Templates

## Estructura del Proyecto

```
powerrent/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── powerrent/                  # Configuración del proyecto
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                       # App base y utilidades
│   ├── models.py              # Mixins reutilizables
│   ├── mixins.py              # Mixins de vistas (admin, cliente)
│   ├── utils.py               # Funciones auxiliares
│   ├── views.py               # Home y páginas generales
│   └── management/commands/
│       └── seed_data.py       # Datos de ejemplo
├── usuarios/                   # App de usuarios
│   ├── models.py              # Modelo Usuario (extiende AbstractUser)
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   └── tests.py
├── equipos/                    # App de equipos
│   ├── models.py              # Categoria, Equipo, ImagenEquipo
│   ├── views.py
│   ├── urls.py
│   ├── filters.py             # Filtros con django-filter
│   ├── services.py            # EquipoService
│   ├── admin.py
│   └── tests.py
├── reservas/                   # App de reservas
│   ├── models.py              # Reserva
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── services.py            # ReservaService
│   ├── admin.py
│   └── tests.py
├── pagos/                      # App de pagos
│   ├── models.py              # Pago
│   ├── views.py
│   ├── urls.py
│   ├── services.py            # PagoService
│   ├── admin.py
│   └── tests.py
├── templates/                  # Templates HTML
│   ├── base.html
│   ├── home.html
│   ├── equipos/
│   ├── reservas/
│   ├── pagos/
│   └── usuarios/
├── static/
└── media/
```

## Modelos de Datos

### Usuario (usuarios/models.py)
- Extiende `AbstractUser` de Django
- Campo `tipo_usuario`: `cliente` o `administrador`
- UUID como primary key
- Campos: teléfono, dirección, ciudad, código postal
- Verificación de email y teléfono
- Métodos: `es_administrador`, `es_cliente`, `puede_gestionar_equipos()`, `puede_realizar_reservas()`

### Categoria (equipos/models.py)
- UUID como primary key
- Nombre, slug (auto-generado), descripción, imagen
- Properties: `total_equipos`, `equipos_disponibles`

### Equipo (equipos/models.py)
- UUID como primary key
- Relación con Categoría (PROTECT)
- Estados: disponible, rentado, mantenimiento, fuera_servicio
- Precios: por día, por semana, por mes
- Depósito de garantía
- Especificaciones técnicas (JSONField)
- Métodos: `consultar_disponibilidad()`, `calcular_precio()`, `marcar_como_rentado()`, `marcar_como_disponible()`

### Reserva (reservas/models.py)
- UUID como primary key
- Número de reserva auto-generado (RES-XXXXXXXXXX)
- Estados: pendiente, confirmada, en_curso, completada, cancelada, vencida
- Costos: alquiler, depósito, adicional (por retrasos o daños)
- Métodos: `confirmar_reserva()`, `iniciar_alquiler()`, `completar_alquiler()`, `cancelar_reserva()`

### Pago (pagos/models.py)
- UUID como primary key
- Número de transacción auto-generado (TXN-XXXXXXXXXXXX)
- Métodos de pago: efectivo, tarjeta crédito/débito, transferencia, PayPal, Stripe
- Estados: pendiente, procesando, completado, fallido, reembolsado
- Tipos: alquiler, depósito, adicional, reembolso

## Instalación con Docker

### Requisitos previos
- Docker Desktop instalado
- Docker Compose v2+

### Pasos

```bash
# 1. Ir a la carpeta del proyecto
cd powerrent

# 2. Levantar los contenedores
docker-compose up --build

# 3. (En otra terminal) Crear datos de ejemplo
docker-compose exec web python manage.py seed_data

# 4. Abrir en el navegador
# http://localhost:8000
```

### Accesos por defecto (después de seed_data)
| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Administrador | `admin` | `admin123` |
| Cliente | `cliente1` | `cliente123` |

### Admin Django
- URL: http://localhost:8000/admin/
- Usuario: `admin` / `admin123`

## Comandos Útiles

```bash
# Levantar en background
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener
docker-compose down

# Correr migraciones
docker-compose exec web python manage.py migrate

# Correr tests
docker-compose exec web python manage.py test

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Shell Django
docker-compose exec web python manage.py shell

# Limpiar todo (incluyendo volúmenes de base de datos)
docker-compose down -v
```

## Flujo del Negocio

1. **Cliente** se registra en el sistema
2. **Cliente** busca equipos disponibles (filtro por categoría, precio, nombre)
3. **Cliente** selecciona un equipo y elige fechas → Sistema calcula el precio automáticamente
4. **Cliente** crea la reserva (queda en estado "Pendiente")
5. **Cliente** realiza el pago (efectivo, tarjeta, transferencia, etc.)
6. **Administrador** confirma la reserva (o el sistema automáticamente si el pago es online)
7. **Administrador** registra la entrega del equipo (estado "En Curso")
8. **Administrador** registra la devolución (estado "Completada")
9. Si hay retraso, se aplica cargo adicional (50% del precio diario por cada día)

## Tests

```bash
# Correr todos los tests
docker-compose exec web python manage.py test

# Tests de una app específica
docker-compose exec web python manage.py test usuarios
docker-compose exec web python manage.py test equipos
docker-compose exec web python manage.py test reservas
docker-compose exec web python manage.py test pagos
```
