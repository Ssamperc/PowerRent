"""
Comando de gestión para poblar la base de datos con datos de ejemplo.

Uso:
    docker-compose exec web python manage.py seed_data

O en desarrollo local:
    python manage.py seed_data

Crea:
  - Usuario administrador: admin / admin123
  - 3 clientes de prueba: cliente1 / cliente123, cliente2 / cliente123, cliente3 / cliente123
  - 6 categorías de equipos
  - 8 equipos con especificaciones técnicas reales
  - 1 bloqueo de disponibilidad de ejemplo
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para PowerRent (usuarios, categorías, equipos, bloqueos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Elimina todos los datos existentes antes de crear los nuevos'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=' * 55))
        self.stdout.write(self.style.HTTP_INFO('  PowerRent — Cargando datos de ejemplo'))
        self.stdout.write(self.style.HTTP_INFO('=' * 55))

        from usuarios.models import Usuario
        from equipos.models import Categoria, Equipo, BloqueoDisponibilidad

        # ─── Usuarios ────────────────────────────────────────────
        self.stdout.write('\n👤 Creando usuarios...')

        admin = None
        if not Usuario.objects.filter(username='admin').exists():
            admin = Usuario.objects.create_superuser(
                username='admin',
                email='admin@powerrent.co',
                password='admin123',
                first_name='Administrador',
                last_name='PowerRent',
                tipo_usuario=Usuario.TipoUsuario.ADMINISTRADOR,
                telefono='+57 300 000 0001',
                ciudad='Bogotá',
            )
            self.stdout.write(self.style.SUCCESS('  ✅ admin / admin123 (superusuario)'))
        else:
            admin = Usuario.objects.get(username='admin')
            self.stdout.write('  ℹ️  admin ya existe')

        clientes_data = [
            ('cliente1', 'carlos.ramirez@test.com', 'Carlos', 'Ramírez', '+57 300 123 4567', 'Bogotá'),
            ('cliente2', 'ana.gomez@test.com', 'Ana', 'Gómez', '+57 311 234 5678', 'Medellín'),
            ('cliente3', 'juan.perez@test.com', 'Juan', 'Pérez', '+57 321 345 6789', 'Cali'),
        ]

        clientes = {}
        for username, email, fname, lname, tel, ciudad in clientes_data:
            if not Usuario.objects.filter(username=username).exists():
                c = Usuario.objects.create_user(
                    username=username, email=email, password='cliente123',
                    first_name=fname, last_name=lname,
                    tipo_usuario=Usuario.TipoUsuario.CLIENTE,
                    telefono=tel, ciudad=ciudad,
                )
                clientes[username] = c
                self.stdout.write(self.style.SUCCESS(f'  ✅ {username} / cliente123'))
            else:
                clientes[username] = Usuario.objects.get(username=username)
                self.stdout.write(f'  ℹ️  {username} ya existe')

        # ─── Categorías ───────────────────────────────────────────
        self.stdout.write('\n📂 Creando categorías...')

        categorias_data = [
            ('Herramientas Eléctricas', 'Taladros, sierras, lijadoras, amoladoras y más', 1),
            ('Compactación', 'Placas compactadoras, apisonadoras, rodillos', 2),
            ('Mezcla y Concreto', 'Mezcladoras, concreteras, vibradoras de inmersión', 3),
            ('Elevación y Andamios', 'Andamios, escaleras extensibles, elevadores de personal', 4),
            ('Corte y Demolición', 'Cortadoras de piso, martillos demoledores, pulidoras', 5),
            ('Bombeo', 'Bombas de agua, motobombas para achique y traslado', 6),
        ]

        categorias = {}
        for nombre, descripcion, orden in categorias_data:
            cat, created = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion, 'orden': orden}
            )
            categorias[nombre] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {nombre}'))
            else:
                self.stdout.write(f'  ℹ️  {nombre} ya existe')

        # ─── Equipos ──────────────────────────────────────────────
        self.stdout.write('\n🔧 Creando equipos...')

        equipos_data = [
            {
                'nombre': 'Taladro Percutor Bosch GSB 550',
                'descripcion': (
                    'Taladro percutor profesional de 550W ideal para trabajos en mampostería, madera y metal. '
                    'Con control de velocidad variable y función de percusión. Incluye maletín y set de brocas.'
                ),
                'categoria': 'Herramientas Eléctricas',
                'codigo_interno': 'TAL-001',
                'marca': 'Bosch',
                'modelo': 'GSB 550',
                'precio_por_dia': Decimal('25000'),
                'precio_por_semana': Decimal('150000'),
                'precio_por_mes': Decimal('500000'),
                'deposito_garantia': Decimal('50000'),
                'especificaciones': {
                    'Potencia': '550W',
                    'Voltaje': '120V',
                    'Velocidad máxima': '2800 RPM',
                    'Capacidad en concreto': '13mm',
                    'Peso': '1.8 kg'
                },
            },
            {
                'nombre': 'Sierra Circular DeWalt DWE575',
                'descripcion': (
                    'Sierra circular de 7-1/4" con motor de 15 amperios. Perfecta para cortes precisos '
                    'en madera, OSB y MDF. Zapata de aluminio ajustable de 0° a 57°.'
                ),
                'categoria': 'Herramientas Eléctricas',
                'codigo_interno': 'SCI-001',
                'marca': 'DeWalt',
                'modelo': 'DWE575',
                'precio_por_dia': Decimal('35000'),
                'precio_por_semana': Decimal('210000'),
                'precio_por_mes': Decimal('700000'),
                'deposito_garantia': Decimal('80000'),
                'especificaciones': {
                    'Potencia': '1800W',
                    'Amperaje': '15A',
                    'Diámetro disco': '7-1/4"',
                    'Profundidad de corte a 90°': '65mm',
                    'RPM': '5200'
                },
            },
            {
                'nombre': 'Placa Compactadora Mikasa MVC-F70',
                'descripcion': (
                    'Placa compactadora reversible de 70cm para compactación de suelos granulares y cohesivos. '
                    'Motor Honda GX160 a gasolina. Ideal para bases de concreto y asfalto.'
                ),
                'categoria': 'Compactación',
                'codigo_interno': 'COM-001',
                'marca': 'Mikasa',
                'modelo': 'MVC-F70',
                'precio_por_dia': Decimal('120000'),
                'precio_por_semana': Decimal('720000'),
                'precio_por_mes': Decimal('2400000'),
                'deposito_garantia': Decimal('500000'),
                'especificaciones': {
                    'Motor': 'Honda GX160 (5.5HP)',
                    'Anchura de placa': '700mm',
                    'Fuerza de compactación': '22 kN',
                    'Frecuencia de vibración': '90 Hz',
                    'Combustible': 'Gasolina'
                },
            },
            {
                'nombre': 'Mezcladora de Concreto 1 Saco',
                'descripcion': (
                    'Mezcladora eléctrica de tambor para 1 saco de cemento (50 kg). '
                    'Capacidad de 120 litros. Ideal para obras pequeñas y medianas. '
                    'Incluye tambor en acero y motor eléctrico monofásico.'
                ),
                'categoria': 'Mezcla y Concreto',
                'codigo_interno': 'MEZ-001',
                'marca': 'Cipsa',
                'modelo': 'CM-1',
                'precio_por_dia': Decimal('80000'),
                'precio_por_semana': Decimal('480000'),
                'precio_por_mes': Decimal('1600000'),
                'deposito_garantia': Decimal('300000'),
                'especificaciones': {
                    'Capacidad': '120 litros',
                    'Motor': '1HP monofásico',
                    'Voltaje': '120V / 60Hz',
                    'Material tambor': 'Acero',
                    'Peso': '95 kg'
                },
            },
            {
                'nombre': 'Sistema de Andamio Multidireccional 2x2m',
                'descripcion': (
                    'Sistema de andamiaje multidireccional Layher Allround en acero galvanizado. '
                    'Incluye tablones de aluminio, marcos verticales, crucetas y bases regulables. '
                    'Altura máxima: 12m. Capacidad: 200 kg/m².'
                ),
                'categoria': 'Elevación y Andamios',
                'codigo_interno': 'AND-001',
                'marca': 'Layher',
                'modelo': 'Allround',
                'precio_por_dia': Decimal('45000'),
                'precio_por_semana': Decimal('270000'),
                'precio_por_mes': Decimal('900000'),
                'deposito_garantia': Decimal('200000'),
                'especificaciones': {
                    'Material': 'Acero galvanizado',
                    'Módulo base': '2x2m',
                    'Altura máxima': '12m',
                    'Capacidad de carga': '200 kg/m²',
                    'Norma': 'DIN EN 12811'
                },
            },
            {
                'nombre': 'Martillo Demoledor Bosch GSH 11 E',
                'descripcion': (
                    'Martillo demoledor eléctrico de 1500W con energía de golpe de 23 julios. '
                    'Para demolición de concreto, asfalto y remoción de materiales. '
                    'Sistema de absorción de vibraciones anti-fatiga. Peso 11.7 kg.'
                ),
                'categoria': 'Corte y Demolición',
                'codigo_interno': 'MAR-001',
                'marca': 'Bosch',
                'modelo': 'GSH 11 E',
                'precio_por_dia': Decimal('90000'),
                'precio_por_semana': Decimal('540000'),
                'precio_por_mes': Decimal('1800000'),
                'deposito_garantia': Decimal('400000'),
                'especificaciones': {
                    'Potencia': '1500W',
                    'Energía de golpe': '23J',
                    'Frecuencia de golpes': '900/min',
                    'Portaherramientas': 'SDS-max',
                    'Peso': '11.7 kg'
                },
            },
            {
                'nombre': 'Motobomba Honda WB20XD',
                'descripcion': (
                    'Motobomba de 2" para achique, traslado y riego de agua limpia. '
                    'Motor Honda GX160 4 tiempos. Caudal máximo: 600 l/min. '
                    'Altura de aspiración: 7m. Ideal para obras con presencia de agua.'
                ),
                'categoria': 'Bombeo',
                'codigo_interno': 'BOM-001',
                'marca': 'Honda',
                'modelo': 'WB20XD',
                'precio_por_dia': Decimal('55000'),
                'precio_por_semana': Decimal('330000'),
                'precio_por_mes': Decimal('1100000'),
                'deposito_garantia': Decimal('250000'),
                'especificaciones': {
                    'Motor': 'Honda GX160 (5.5HP)',
                    'Diámetro de succión/descarga': '2" (50mm)',
                    'Caudal máximo': '600 l/min',
                    'Altura de aspiración': '7m',
                    'Combustible': 'Gasolina'
                },
            },
            {
                'nombre': 'Cortadora de Piso Stihl TS 420',
                'descripcion': (
                    'Cortadora de disco para concreto armado, asfalto y piedra natural. '
                    'Disco de diamante de 12" (300mm). Motor a gasolina de 3.2HP. '
                    'Profundidad de corte: 115mm. Incluye guía de agua para reducción de polvo.'
                ),
                'categoria': 'Corte y Demolición',
                'codigo_interno': 'COR-001',
                'marca': 'Stihl',
                'modelo': 'TS 420',
                'precio_por_dia': Decimal('100000'),
                'precio_por_semana': Decimal('600000'),
                'precio_por_mes': Decimal('2000000'),
                'deposito_garantia': Decimal('450000'),
                'especificaciones': {
                    'Motor': '3.2HP (2.4 kW) a gasolina',
                    'Diámetro de disco': '12" (300mm)',
                    'Profundidad de corte': '115mm',
                    'Velocidad disco': '5350 RPM',
                    'Combustible': 'Gasolina (mezcla 2T)'
                },
            },
        ]

        equipos_creados = {}
        for data in equipos_data:
            cat_nombre = data.pop('categoria')
            equipo, created = Equipo.objects.get_or_create(
                codigo_interno=data['codigo_interno'],
                defaults={**data, 'categoria': categorias[cat_nombre]}
            )
            equipos_creados[data['codigo_interno']] = equipo
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {equipo.nombre}'))
            else:
                self.stdout.write(f'  ℹ️  {equipo.nombre} ya existe')

        # ─── Bloqueos de disponibilidad ───────────────────────────
        self.stdout.write('\n🔒 Creando bloqueos de disponibilidad...')

        hoy = timezone.now().date()

        bloqueo_data = [
            {
                'equipo': equipos_creados.get('COM-001'),
                'fecha_inicio': hoy + timedelta(days=10),
                'fecha_fin': hoy + timedelta(days=15),
                'tipo_motivo': 'mantenimiento',
                'motivo': 'Mantenimiento preventivo programado - cambio de filtros y aceite motor Honda',
            },
            {
                'equipo': equipos_creados.get('MAR-001'),
                'fecha_inicio': hoy + timedelta(days=20),
                'fecha_fin': hoy + timedelta(days=22),
                'tipo_motivo': 'inspeccion',
                'motivo': 'Inspección técnica de seguridad - verificación de absorbedor de vibraciones',
            },
        ]

        for bd in bloqueo_data:
            equipo = bd.get('equipo')
            if equipo:
                exists = BloqueoDisponibilidad.objects.filter(
                    equipo=equipo,
                    fecha_inicio=bd['fecha_inicio']
                ).exists()
                if not exists:
                    BloqueoDisponibilidad.objects.create(
                        equipo=equipo,
                        fecha_inicio=bd['fecha_inicio'],
                        fecha_fin=bd['fecha_fin'],
                        tipo_motivo=bd['tipo_motivo'],
                        motivo=bd['motivo'],
                        creado_por=admin,
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Bloqueo: {equipo.nombre} ({bd["tipo_motivo"]})'))

        # ─── Resumen final ────────────────────────────────────────
        self.stdout.write('\n' + '=' * 55)
        self.stdout.write(self.style.SUCCESS('✅ Datos de ejemplo cargados exitosamente'))
        self.stdout.write('=' * 55)
        self.stdout.write('\n🔑 Credenciales de acceso:')
        self.stdout.write(self.style.WARNING('  Admin     → admin / admin123'))
        self.stdout.write('  Cliente 1 → cliente1 / cliente123 (Carlos Ramírez)')
        self.stdout.write('  Cliente 2 → cliente2 / cliente123 (Ana Gómez)')
        self.stdout.write('  Cliente 3 → cliente3 / cliente123 (Juan Pérez)')
        self.stdout.write('\n🌐 URLs:')
        self.stdout.write('  Sitio:     http://localhost:8000/')
        self.stdout.write('  Admin:     http://localhost:8000/admin/')
        self.stdout.write('  Dashboard: http://localhost:8000/dashboard/')
        self.stdout.write('  Equipos:   http://localhost:8000/equipos/')
        self.stdout.write('')
