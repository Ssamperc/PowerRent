from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from usuarios.models import Usuario
from equipos.models import Categoria, Equipo
from reservas.models import Reserva
from .models import Pago
from .services import PagoService


class PagoModelTest(TestCase):
    """Tests para el modelo Pago"""

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
            deposito_garantia=Decimal('50000'),
        )
        self.reserva = Reserva.objects.create(
            cliente=self.cliente,
            equipo=self.equipo,
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=4),
            costo_alquiler=Decimal('75000'),
        )

    def test_crear_pago_numero_transaccion_generado(self):
        """El número de transacción se genera automáticamente con prefijo PAY-"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        self.assertIsNotNone(pago.numero_transaccion)
        self.assertTrue(pago.numero_transaccion.startswith('PAY-'))

    def test_estado_inicial_pendiente(self):
        """El estado inicial de un pago es PENDIENTE"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        self.assertEqual(pago.estado, Pago.EstadoPago.PENDIENTE)
        self.assertTrue(pago.es_pendiente)
        self.assertFalse(pago.es_completado)

    def test_procesar_pago_efectivo(self):
        """Procesar un pago en efectivo lo marca como completado"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        resultado = pago.procesar_pago()
        self.assertTrue(resultado)
        self.assertEqual(pago.estado, Pago.EstadoPago.COMPLETADO)
        self.assertIsNotNone(pago.fecha_procesado)
        self.assertTrue(pago.es_completado)

    def test_procesar_pago_ya_completado_falla(self):
        """No se puede procesar un pago que ya fue completado"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        pago.procesar_pago()  # Primer proceso
        with self.assertRaises(ValueError):
            pago.procesar_pago()  # Segundo proceso debe fallar

    def test_reembolsar_pago(self):
        """Reembolsar un pago completado crea un pago de reembolso y marca el original como reembolsado"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        pago.procesar_pago()

        pago_reembolso = pago.reembolsar(motivo='Cancelación del cliente')

        self.assertEqual(pago.estado, Pago.EstadoPago.REEMBOLSADO)
        self.assertEqual(pago_reembolso.tipo_pago, Pago.TipoPago.REEMBOLSO)
        self.assertEqual(pago_reembolso.monto, Decimal('75000'))

    def test_reembolsar_pago_pendiente_falla(self):
        """No se puede reembolsar un pago pendiente"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        with self.assertRaises(ValueError):
            pago.reembolsar()

    def test_monto_usa_decimal(self):
        """El monto debe ser DecimalField (no float/double)"""
        pago = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.cliente,
            monto=Decimal('75000'),
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=Pago.MetodoPago.EFECTIVO,
        )
        self.assertIsInstance(pago.monto, Decimal)


class PagoServiceTest(TestCase):
    """Tests para el servicio PagoService"""

    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente2',
            email='cliente2@test.com',
            password='testpass123',
            tipo_usuario=Usuario.TipoUsuario.CLIENTE
        )
        self.categoria = Categoria.objects.create(nombre='Compactación')
        self.equipo = Equipo.objects.create(
            nombre='Placa Compactadora',
            descripcion='Para compactación',
            categoria=self.categoria,
            codigo_interno='COM-001',
            precio_por_dia=Decimal('100000'),
            deposito_garantia=Decimal('200000'),
        )
        self.reserva = Reserva.objects.create(
            cliente=self.cliente,
            equipo=self.equipo,
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=4),
            costo_alquiler=Decimal('300000'),
        )

    def test_procesar_pago_completo_crea_dos_pagos(self):
        """procesar_pago_completo crea pago de alquiler + pago de depósito"""
        resultados = PagoService.procesar_pago_completo(
            reserva=self.reserva,
            usuario=self.cliente,
            metodo_pago=Pago.MetodoPago.EFECTIVO
        )
        self.assertIn('alquiler', resultados)
        self.assertIn('deposito', resultados)
        self.assertEqual(resultados['alquiler'].monto, Decimal('300000'))
        self.assertEqual(resultados['deposito'].monto, Decimal('200000'))

    def test_procesar_pago_completo_confirma_reserva(self):
        """Al completar el pago, la reserva debe pasar a confirmada"""
        PagoService.procesar_pago_completo(
            reserva=self.reserva,
            usuario=self.cliente,
            metodo_pago=Pago.MetodoPago.EFECTIVO
        )
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.EstadoReserva.CONFIRMADA)
