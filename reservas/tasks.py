"""
Tareas periódicas para el módulo de reservas.

En producción estas tareas se ejecutan con Celery + Redis o con cron jobs.
Para desarrollo se pueden invocar manualmente desde el shell de Django:

    python manage.py shell
    >>> from reservas.tasks import *
    >>> verificar_reservas_vencidas()
    >>> enviar_recordatorios_entrega()

Para Celery, configurar en settings:
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
"""

from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def verificar_reservas_vencidas():
    """
    Tarea: Marca como vencidas las reservas en curso que ya pasaron su fecha de fin.
    Debe ejecutarse diariamente (ej: cada hora con cron o Celery beat).

    Returns:
        int: Número de reservas marcadas como vencidas
    """
    from .services import ReservaService

    count = ReservaService.marcar_reservas_vencidas()

    if count > 0:
        logger.warning(f"Se marcaron {count} reservas como vencidas")

    return count


def enviar_recordatorios_entrega():
    """
    Tarea: Envía recordatorios a clientes con reservas confirmadas que inician mañana.
    Debe ejecutarse diariamente (ej: a las 8am).

    Returns:
        int: Número de recordatorios enviados
    """
    from .services import ReservaService
    from core.utils import enviar_email_notificacion

    reservas_manana = ReservaService.obtener_reservas_proximas(dias=1)
    count = 0

    for reserva in reservas_manana:
        if reserva.fecha_inicio == timezone.now().date() + timedelta(days=1):
            asunto = f'Recordatorio: Tu alquiler de {reserva.equipo.nombre} comienza mañana'
            mensaje = (
                f'Hola {reserva.cliente.get_full_name() or reserva.cliente.username},\n\n'
                f'Te recordamos que mañana ({reserva.fecha_inicio}) comienza tu reserva:\n'
                f'  • Equipo: {reserva.equipo.nombre}\n'
                f'  • Código: {reserva.equipo.codigo_interno}\n'
                f'  • Período: {reserva.fecha_inicio} → {reserva.fecha_fin}\n'
                f'  • Reserva: {reserva.numero_reserva}\n\n'
                f'Por favor asegúrate de estar disponible para recibir el equipo.\n\n'
                f'Equipo PowerRent'
            )
            enviado = enviar_email_notificacion(reserva.cliente.email, asunto, mensaje)
            if enviado:
                count += 1

    logger.info(f"Enviados {count} recordatorios de entrega")
    return count


def enviar_recordatorios_devolucion():
    """
    Tarea: Envía recordatorios a clientes con reservas en curso que vencen mañana.
    Debe ejecutarse diariamente (ej: a las 9am).

    Returns:
        int: Número de recordatorios enviados
    """
    from .models import Reserva
    from core.utils import enviar_email_notificacion

    manana = timezone.now().date() + timedelta(days=1)
    reservas_por_vencer = Reserva.objects.filter(
        estado=Reserva.EstadoReserva.EN_CURSO,
        fecha_fin=manana
    ).select_related('cliente', 'equipo')

    count = 0
    for reserva in reservas_por_vencer:
        asunto = f'Recordatorio: Devolución de {reserva.equipo.nombre} mañana'
        mensaje = (
            f'Hola {reserva.cliente.get_full_name() or reserva.cliente.username},\n\n'
            f'Te recordamos que mañana ({reserva.fecha_fin}) vence tu reserva:\n'
            f'  • Equipo: {reserva.equipo.nombre}\n'
            f'  • Reserva: {reserva.numero_reserva}\n\n'
            f'Por favor devuelve el equipo a tiempo para evitar cargos adicionales.\n'
            f'El cargo por retraso es del 50% del precio diario por día de retraso.\n\n'
            f'Equipo PowerRent'
        )
        enviado = enviar_email_notificacion(reserva.cliente.email, asunto, mensaje)
        if enviado:
            count += 1

    logger.info(f"Enviados {count} recordatorios de devolución")
    return count


def enviar_alerta_mantenimiento():
    """
    Tarea: Notifica al administrador sobre equipos que requieren mantenimiento.
    Debe ejecutarse semanalmente.

    Returns:
        int: Número de equipos alertados
    """
    from equipos.services import EquipoService
    from core.utils import enviar_email_notificacion
    from django.conf import settings

    equipos_mantenimiento = EquipoService.generar_reporte_mantenimiento()
    count = equipos_mantenimiento.count()

    if count > 0:
        lista = '\n'.join([
            f'  • {eq.nombre} ({eq.codigo_interno}) - Próximo mantenimiento: {eq.proxima_fecha_mantenimiento}'
            for eq in equipos_mantenimiento
        ])

        asunto = f'[PowerRent] {count} equipos requieren mantenimiento'
        mensaje = (
            f'Reporte de Mantenimiento - PowerRent\n\n'
            f'Los siguientes {count} equipos requieren mantenimiento:\n\n'
            f'{lista}\n\n'
            f'Por favor programa el mantenimiento lo antes posible.'
        )

        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@powerrent.co')
        enviar_email_notificacion(admin_email, asunto, mensaje)
        logger.warning(f"Alerta de mantenimiento: {count} equipos")

    return count
