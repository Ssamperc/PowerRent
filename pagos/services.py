from decimal import Decimal
from django.db.models import Sum
from .models import Pago
from reservas.models import Reserva


class PagoService:
    """Servicio para gestión de pagos"""

    @staticmethod
    def crear_pago_alquiler(reserva, usuario, metodo_pago):
        """
        Crea el pago principal de una reserva

        Args:
            reserva: Instancia de Reserva
            usuario: Usuario que realiza el pago
            metodo_pago: Método de pago seleccionado

        Returns:
            Pago creado
        """
        pago = Pago.objects.create(
            reserva=reserva,
            usuario=usuario,
            monto=reserva.costo_alquiler,
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=metodo_pago,
        )
        return pago

    @staticmethod
    def crear_pago_deposito(reserva, usuario, metodo_pago):
        """
        Crea el pago de depósito de garantía

        Args:
            reserva: Instancia de Reserva
            usuario: Usuario que realiza el pago
            metodo_pago: Método de pago seleccionado

        Returns:
            Pago creado
        """
        if reserva.equipo.deposito_garantia <= 0:
            return None

        pago = Pago.objects.create(
            reserva=reserva,
            usuario=usuario,
            monto=reserva.equipo.deposito_garantia,
            tipo_pago=Pago.TipoPago.DEPOSITO,
            metodo_pago=metodo_pago,
        )
        return pago

    @staticmethod
    def procesar_pago_completo(reserva, usuario, metodo_pago):
        """
        Procesa el pago completo de una reserva (alquiler + depósito)

        Returns:
            dict con los pagos realizados
        """
        resultados = {}

        pago_alquiler = PagoService.crear_pago_alquiler(reserva, usuario, metodo_pago)
        pago_alquiler.procesar_pago()
        resultados['alquiler'] = pago_alquiler

        pago_deposito = PagoService.crear_pago_deposito(reserva, usuario, metodo_pago)
        if pago_deposito:
            pago_deposito.procesar_pago()
            resultados['deposito'] = pago_deposito

        # Si el pago fue exitoso, confirmar la reserva
        if pago_alquiler.es_completado:
            try:
                reserva.confirmar_reserva()
                resultados['reserva_confirmada'] = True
            except ValueError as e:
                resultados['error'] = str(e)

        return resultados

    @staticmethod
    def obtener_ingresos_totales():
        """Retorna los ingresos totales de pagos completados"""
        return Pago.objects.filter(
            estado=Pago.EstadoPago.COMPLETADO,
            tipo_pago=Pago.TipoPago.ALQUILER
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    @staticmethod
    def obtener_pagos_pendientes():
        """Retorna todos los pagos pendientes"""
        return Pago.objects.filter(
            estado=Pago.EstadoPago.PENDIENTE
        ).select_related('reserva', 'usuario', 'reserva__equipo')
