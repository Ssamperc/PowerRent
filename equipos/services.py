from datetime import timedelta
from django.db.models import Count, Q, Avg
from django.utils import timezone
from .models import Equipo, Categoria, BloqueoDisponibilidad


class EquipoService:
    """Servicio para gestión de equipos - lógica de negocio"""

    @staticmethod
    def buscar_equipos_disponibles(fecha_inicio, fecha_fin, categoria=None, precio_max=None):
        """
        Busca equipos disponibles para un rango de fechas.
        Considera reservas activas Y bloqueos de disponibilidad.

        Args:
            fecha_inicio: Fecha de inicio del alquiler
            fecha_fin: Fecha de fin del alquiler
            categoria: Objeto Categoria para filtrar (opcional)
            precio_max: Precio máximo por día (opcional)

        Returns:
            QuerySet de Equipos disponibles
        """
        equipos = Equipo.objects.filter(
            activo=True,
            disponible=True,
            estado=Equipo.EstadoEquipo.DISPONIBLE
        ).select_related('categoria')

        if categoria:
            equipos = equipos.filter(categoria=categoria)

        if precio_max:
            equipos = equipos.filter(precio_por_dia__lte=precio_max)

        # Filtrar equipos con reservas que se solapen en las fechas
        equipos_disponibles = [
            equipo.id
            for equipo in equipos
            if equipo.consultar_disponibilidad(fecha_inicio, fecha_fin)
        ]

        return equipos.filter(id__in=equipos_disponibles)

    @staticmethod
    def obtener_equipos_populares(limit=10):
        """
        Obtiene los equipos más rentados (por cantidad de reservas completadas)

        Returns:
            QuerySet de Equipos anotados con total_reservas
        """
        return Equipo.objects.annotate(
            total_reservas=Count('reservas')
        ).filter(activo=True).order_by('-total_reservas')[:limit]

    @staticmethod
    def calcular_tasa_ocupacion(equipo, dias=30):
        """
        Calcula la tasa de ocupación de un equipo en los últimos N días.

        Args:
            equipo: Instancia de Equipo
            dias: Número de días a analizar (default: 30)

        Returns:
            float: Porcentaje de ocupación (0.0 - 100.0)
        """
        from reservas.models import Reserva

        fecha_inicio = timezone.now().date() - timedelta(days=dias)
        fecha_fin = timezone.now().date()

        reservas = Reserva.objects.filter(
            equipo=equipo,
            estado__in=[Reserva.EstadoReserva.CONFIRMADA, Reserva.EstadoReserva.COMPLETADA,
                        Reserva.EstadoReserva.EN_CURSO],
            fecha_inicio__gte=fecha_inicio,
            fecha_fin__lte=fecha_fin
        )

        dias_rentados = sum(r.dias_alquiler for r in reservas)

        if dias == 0:
            return 0.0

        return min((dias_rentados / dias) * 100, 100.0)

    @staticmethod
    def generar_reporte_mantenimiento():
        """
        Genera reporte de equipos que requieren o están en mantenimiento.

        Returns:
            QuerySet de Equipos
        """
        return Equipo.objects.filter(
            Q(proxima_fecha_mantenimiento__lte=timezone.now().date()) |
            Q(estado=Equipo.EstadoEquipo.MANTENIMIENTO)
        ).select_related('categoria').order_by('proxima_fecha_mantenimiento')

    @staticmethod
    def crear_bloqueo(equipo, fecha_inicio, fecha_fin, tipo_motivo, motivo, admin):
        """
        Crea un bloqueo de disponibilidad para un equipo.

        Args:
            equipo: Equipo a bloquear
            fecha_inicio: Fecha inicio del bloqueo
            fecha_fin: Fecha fin del bloqueo
            tipo_motivo: Tipo de motivo (mantenimiento, reparacion, etc.)
            motivo: Descripción del motivo
            admin: Usuario administrador que crea el bloqueo

        Returns:
            BloqueoDisponibilidad creado
        """
        from django.core.exceptions import ValidationError

        if fecha_inicio >= fecha_fin:
            raise ValidationError("La fecha de fin debe ser posterior a la de inicio")

        bloqueo = BloqueoDisponibilidad.objects.create(
            equipo=equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_motivo=tipo_motivo,
            motivo=motivo,
            creado_por=admin,
        )

        # Si el bloqueo inicia hoy o es inmediato, actualizar estado del equipo
        if fecha_inicio <= timezone.now().date():
            equipo.enviar_a_mantenimiento(motivo)

        return bloqueo

    @staticmethod
    def obtener_calificacion_promedio(equipo):
        """
        Obtiene la calificación promedio de un equipo.

        Returns:
            float: Promedio (1-5) o None si no tiene calificaciones
        """
        from .models import CalificacionEquipo
        result = CalificacionEquipo.objects.filter(equipo=equipo).aggregate(promedio=Avg('puntuacion'))
        return result['promedio']
