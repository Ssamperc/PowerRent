from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from .models import Categoria, Equipo, BloqueoDisponibilidad


class CategoriaModelTest(TestCase):
    """Tests para el modelo Categoria"""

    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre='Herramientas Eléctricas',
            descripcion='Taladros, sierras, etc.'
        )

    def test_categoria_str(self):
        self.assertEqual(str(self.categoria), 'Herramientas Eléctricas')

    def test_slug_auto_generado(self):
        self.assertEqual(self.categoria.slug, 'herramientas-electricas')

    def test_total_equipos_vacio(self):
        self.assertEqual(self.categoria.total_equipos, 0)


class EquipoModelTest(TestCase):
    """Tests para el modelo Equipo"""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Herramientas')
        self.equipo = Equipo.objects.create(
            nombre='Taladro Bosch 500W',
            descripcion='Taladro percutor profesional',
            categoria=self.categoria,
            codigo_interno='TAL-001',
            precio_por_dia=Decimal('25000'),
            precio_por_semana=Decimal('150000'),
            precio_por_mes=Decimal('500000'),
            deposito_garantia=Decimal('50000'),
        )

    def test_equipo_str(self):
        self.assertIn('TAL-001', str(self.equipo))

    def test_slug_auto_generado(self):
        self.assertIn('taladro', self.equipo.slug)

    def test_calcular_precio_diario(self):
        """Precio para 3 días = precio_dia * 3"""
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=3)
        precio = self.equipo.calcular_precio(fecha_inicio, fecha_fin)
        self.assertEqual(precio, Decimal('75000'))

    def test_calcular_precio_semanal(self):
        """7 días usa precio_por_semana si está configurado"""
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=7)
        precio = self.equipo.calcular_precio(fecha_inicio, fecha_fin)
        self.assertEqual(precio, Decimal('150000'))

    def test_calcular_precio_mensual(self):
        """30 días usa precio_por_mes si está configurado"""
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=30)
        precio = self.equipo.calcular_precio(fecha_inicio, fecha_fin)
        self.assertEqual(precio, Decimal('500000'))

    def test_calcular_precio_sin_descuento_especial(self):
        """Sin precio semanal/mensual configurado, usa precio diario"""
        equipo = Equipo.objects.create(
            nombre='Equipo sin descuento',
            descripcion='Test',
            categoria=self.categoria,
            codigo_interno='TEST-001',
            precio_por_dia=Decimal('10000'),
        )
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=7)
        precio = equipo.calcular_precio(fecha_inicio, fecha_fin)
        self.assertEqual(precio, Decimal('70000'))

    def test_marcar_como_rentado(self):
        self.equipo.marcar_como_rentado()
        self.assertFalse(self.equipo.disponible)
        self.assertEqual(self.equipo.estado, Equipo.EstadoEquipo.RENTADO)

    def test_marcar_como_disponible(self):
        self.equipo.marcar_como_rentado()
        self.equipo.marcar_como_disponible()
        self.assertTrue(self.equipo.disponible)
        self.assertEqual(self.equipo.estado, Equipo.EstadoEquipo.DISPONIBLE)

    def test_consultar_disponibilidad_equipo_libre(self):
        """Equipo sin reservas debe estar disponible"""
        fecha_inicio = date.today() + timedelta(days=5)
        fecha_fin = fecha_inicio + timedelta(days=3)
        self.assertTrue(self.equipo.consultar_disponibilidad(fecha_inicio, fecha_fin))

    def test_consultar_disponibilidad_equipo_no_disponible(self):
        """Equipo marcado como no disponible retorna False"""
        self.equipo.disponible = False
        self.equipo.save()
        fecha_inicio = date.today() + timedelta(days=5)
        fecha_fin = fecha_inicio + timedelta(days=3)
        self.assertFalse(self.equipo.consultar_disponibilidad(fecha_inicio, fecha_fin))

    def test_deposito_garantia_decimal(self):
        """Depósito usa DecimalField (no float/double)"""
        from decimal import Decimal
        self.assertIsInstance(self.equipo.deposito_garantia, Decimal)
        self.assertIsInstance(self.equipo.precio_por_dia, Decimal)


class BloqueoDisponibilidadTest(TestCase):
    """Tests para el modelo BloqueoDisponibilidad"""

    def setUp(self):
        from usuarios.models import Usuario
        self.categoria = Categoria.objects.create(nombre='Test')
        self.equipo = Equipo.objects.create(
            nombre='Equipo Bloqueo',
            descripcion='Para prueba de bloqueos',
            categoria=self.categoria,
            codigo_interno='BLQ-001',
            precio_por_dia=Decimal('50000'),
        )
        self.admin = Usuario.objects.create_superuser(
            username='testadmin', email='admin@test.com', password='pass123',
            tipo_usuario='administrador'
        )

    def test_bloqueo_impide_disponibilidad(self):
        """Un bloqueo activo debe impedir reservar en esas fechas"""
        hoy = date.today()
        BloqueoDisponibilidad.objects.create(
            equipo=self.equipo,
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=10),
            tipo_motivo='mantenimiento',
            motivo='Mantenimiento programado',
            creado_por=self.admin,
        )
        # Intentar reservar dentro del bloqueo
        self.assertFalse(
            self.equipo.consultar_disponibilidad(
                hoy + timedelta(days=6),
                hoy + timedelta(days=8)
            )
        )

    def test_bloqueo_inactivo_permite_reserva(self):
        """Un bloqueo inactivo NO debe impedir reservas"""
        hoy = date.today()
        BloqueoDisponibilidad.objects.create(
            equipo=self.equipo,
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=10),
            tipo_motivo='mantenimiento',
            motivo='Mantenimiento cancelado',
            activo=False,
            creado_por=self.admin,
        )
        # El bloqueo está inactivo, debería poder reservar
        self.assertTrue(
            self.equipo.consultar_disponibilidad(
                hoy + timedelta(days=6),
                hoy + timedelta(days=8)
            )
        )

    def test_bloqueo_str(self):
        hoy = date.today()
        bloqueo = BloqueoDisponibilidad.objects.create(
            equipo=self.equipo,
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=5),
            tipo_motivo='reparacion',
            motivo='Reparación urgente',
            creado_por=self.admin,
        )
        self.assertIn(self.equipo.nombre, str(bloqueo))
