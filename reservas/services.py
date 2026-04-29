from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Reserva


class ReservaService:
    """Servicio para gestión de reservas - contiene la lógica de negocio principal"""

    @staticmethod
    @transaction.atomic
    def crear_reserva(cliente, equipo, fecha_inicio, fecha_fin, notas=''):
        """
        Crea una nueva reserva verificando disponibilidad.
        Usa @transaction.atomic para garantizar consistencia de datos.

        Args:
            cliente: Usuario que realiza la reserva
            equipo: Equipo a reservar
            fecha_inicio: Fecha de inicio del alquiler
            fecha_fin: Fecha de fin del alquiler
            notas: Notas adicionales del cliente

        Returns:
            Reserva: Reserva creada

        Raises:
            ValueError: Si el equipo no está disponible o los datos son inválidos
        """
        # Validar que el cliente puede realizar reservas
        if not cliente.puede_realizar_reservas():
            raise ValueError("El usuario no tiene permisos para realizar reservas")

        # Validar fechas
        if fecha_inicio >= fecha_fin:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")

        if fecha_inicio < timezone.now().date():
            raise ValueError("No se pueden hacer reservas para fechas pasadas")

        # Verificar disponibilidad del equipo
        if not equipo.consultar_disponibilidad(fecha_inicio, fecha_fin):
            raise ValueError(f"El equipo '{equipo.nombre}' no está disponible para las fechas seleccionadas")

        # Crear la reserva
        reserva = Reserva.objects.create(
            cliente=cliente,
            equipo=equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            notas_cliente=notas,
            deposito_pagado=equipo.deposito_garantia,
        )

        # Calcular costo automáticamente
        reserva.calcular_costo()

        # Enviar notificación al cliente y admins
        try:
            from core.notificaciones import NotificacionService
            NotificacionService.reserva_creada(reserva)
        except Exception:
            pass

        return reserva

    @staticmethod
    @transaction.atomic
    def confirmar_reserva_con_pago(reserva, metodo_pago):
        """
        Confirma una reserva y procesa los pagos correspondientes.
        Crea pago de alquiler + pago de depósito si aplica.

        Args:
            reserva: Reserva a confirmar
            metodo_pago: Método de pago seleccionado

        Returns:
            tuple: (Reserva confirmada, Pago de alquiler)

        Raises:
            ValueError: Si el pago falla o la reserva no puede confirmarse
        """
        from pagos.models import Pago

        # Crear pago del alquiler
        pago_alquiler = Pago.objects.create(
            reserva=reserva,
            usuario=reserva.cliente,
            monto=reserva.costo_alquiler,
            tipo_pago=Pago.TipoPago.ALQUILER,
            metodo_pago=metodo_pago
        )

        # Crear pago del depósito si el equipo requiere depósito
        pago_deposito = None
        if reserva.equipo.deposito_garantia > 0:
            pago_deposito = Pago.objects.create(
                reserva=reserva,
                usuario=reserva.cliente,
                monto=reserva.equipo.deposito_garantia,
                tipo_pago=Pago.TipoPago.DEPOSITO,
                metodo_pago=metodo_pago
            )

        # Procesar pago del alquiler
        if not pago_alquiler.procesar_pago():
            raise ValueError("Error al procesar el pago del alquiler")

        # Procesar pago del depósito
        if pago_deposito and not pago_deposito.procesar_pago():
            raise ValueError("Error al procesar el pago del depósito")

        # Confirmar la reserva (verifica disponibilidad nuevamente)
        reserva.confirmar_reserva()

        # Notificaciones
        try:
            from core.notificaciones import NotificacionService
            NotificacionService.reserva_confirmada(reserva)
            NotificacionService.pago_recibido(pago_alquiler)
        except Exception:
            pass

        return reserva, pago_alquiler

    @staticmethod
    def obtener_reservas_proximas(dias=7):
        """
        Obtiene reservas confirmadas que inician en los próximos N días.
        Usado para enviar recordatorios.

        Returns:
            QuerySet de Reservas
        """
        fecha_limite = timezone.now().date() + timedelta(days=dias)

        return Reserva.objects.filter(
            estado=Reserva.EstadoReserva.CONFIRMADA,
            fecha_inicio__lte=fecha_limite,
            fecha_inicio__gte=timezone.now().date()
        ).select_related('cliente', 'equipo')

    @staticmethod
    def obtener_reservas_vencidas():
        """
        Obtiene reservas en curso cuya fecha de fin ya pasó.
        Estas deberían marcarse como vencidas.

        Returns:
            QuerySet de Reservas
        """
        return Reserva.objects.filter(
            estado=Reserva.EstadoReserva.EN_CURSO,
            fecha_fin__lt=timezone.now().date()
        ).select_related('cliente', 'equipo')

    @staticmethod
    def obtener_reservas_activas():
        """Retorna todas las reservas activas (confirmadas o en curso)"""
        return Reserva.objects.filter(
            estado__in=[Reserva.EstadoReserva.CONFIRMADA, Reserva.EstadoReserva.EN_CURSO]
        ).select_related('cliente', 'equipo', 'equipo__categoria')

    @staticmethod
    def obtener_ingresos_mes(año=None, mes=None):
        """Calcula los ingresos del mes indicado"""
        hoy = timezone.now().date()
        año = año or hoy.year
        mes = mes or hoy.month

        return Reserva.objects.filter(
            estado=Reserva.EstadoReserva.COMPLETADA,
            fecha_fin__year=año,
            fecha_fin__month=mes
        ).aggregate(total=Sum('costo_alquiler'))['total'] or Decimal('0.00')

    @staticmethod
    def obtener_estadisticas():
        """Retorna estadísticas generales del sistema para el dashboard"""
        from equipos.models import Equipo

        return {
            'total_reservas': Reserva.objects.count(),
            'reservas_pendientes': Reserva.objects.filter(estado=Reserva.EstadoReserva.PENDIENTE).count(),
            'reservas_confirmadas': Reserva.objects.filter(estado=Reserva.EstadoReserva.CONFIRMADA).count(),
            'reservas_en_curso': Reserva.objects.filter(estado=Reserva.EstadoReserva.EN_CURSO).count(),
            'reservas_completadas': Reserva.objects.filter(estado=Reserva.EstadoReserva.COMPLETADA).count(),
            'reservas_canceladas': Reserva.objects.filter(estado=Reserva.EstadoReserva.CANCELADA).count(),
            'ingresos_mes': ReservaService.obtener_ingresos_mes(),
            'total_equipos': Equipo.objects.filter(activo=True).count(),
            'equipos_disponibles': Equipo.objects.filter(activo=True, disponible=True).count(),
            'equipos_rentados': Equipo.objects.filter(estado=Equipo.EstadoEquipo.RENTADO).count(),
            'equipos_mantenimiento': Equipo.objects.filter(estado=Equipo.EstadoEquipo.MANTENIMIENTO).count(),
            'reservas_proximas': ReservaService.obtener_reservas_proximas(dias=7),
            'reservas_vencidas': ReservaService.obtener_reservas_vencidas(),
        }

    @staticmethod
    @transaction.atomic
    def marcar_reservas_vencidas():
        """
        Marca como vencidas las reservas en curso cuya fecha fin ya pasó.
        Devuelve el equipo al estado disponible.
        Debe ejecutarse periódicamente (via tarea Celery o cron).
        """
        reservas = ReservaService.obtener_reservas_vencidas()
        count = 0
        for reserva in reservas:
            reserva.estado = Reserva.EstadoReserva.VENCIDA
            reserva.save(update_fields=['estado', 'updated_at'])
            reserva.equipo.marcar_como_disponible()
            count += 1
        return count
