from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from usuarios.models import Usuario
from equipos.models import Categoria, Equipo
from .models import Reserva
from .services import ReservaService


class ReservaModelTest(TestCase):

    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente1',
            email='cliente@test.com',
            password='testpass123',
            tipo_usuario=Usuario.TipoUsuario.CLIENTE
        )
        self.categoria = Categoria.objects.create(nombre='Herramientas')
        self.equipo = Equipo.objects.create(
            nombre='Taladro Pro',
            descripcion='Taladro profesional',
            categoria=self.categoria,
            codigo_interno='TAL-001',
            precio_por_dia=Decimal('25000'),
        )

    def test_crear_reserva_valida(self):
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = fecha_inicio + timedelta(days=3)

        reserva = ReservaService.crear_reserva(
            cliente=self.cliente,
            equipo=self.equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        self.assertIsNotNone(reserva.numero_reserva)
        self.assertTrue(reserva.numero_reserva.startswith('RES-'))
        self.assertEqual(reserva.estado, Reserva.EstadoReserva.PENDIENTE)
        self.assertEqual(reserva.costo_alquiler, Decimal('75000'))

    def test_numero_reserva_unico(self):
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = fecha_inicio + timedelta(days=2)

        r1 = Reserva.objects.create(
            cliente=self.cliente,
            equipo=self.equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        equipo2 = Equipo.objects.create(
            nombre='Sierra',
            descripcion='Sierra eléctrica',
            categoria=self.categoria,
            codigo_interno='SIE-001',
            precio_por_dia=Decimal('30000'),
        )

        r2 = Reserva.objects.create(
            cliente=self.cliente,
            equipo=equipo2,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        self.assertNotEqual(r1.numero_reserva, r2.numero_reserva)

    def test_dias_alquiler(self):
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = fecha_inicio + timedelta(days=5)

        reserva = Reserva.objects.create(
            cliente=self.cliente,
            equipo=self.equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        self.assertEqual(reserva.dias_alquiler, 5)
