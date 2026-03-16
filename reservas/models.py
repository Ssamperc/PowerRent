from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
import random
import string


class Reserva(models.Model):
    """Reserva de equipo"""

    class EstadoReserva(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de Confirmación'
        CONFIRMADA = 'confirmada', 'Confirmada'
        EN_CURSO = 'en_curso', 'En Curso'
        COMPLETADA = 'completada', 'Completada'
        CANCELADA = 'cancelada', 'Cancelada'
        VENCIDA = 'vencida', 'Vencida'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_reserva = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Número de Reserva')

    # Relaciones
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservas',
        limit_choices_to={'tipo_usuario': 'cliente'},
        verbose_name='Cliente'
    )
    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='reservas',
        verbose_name='Equipo'
    )

    # Fechas
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    fecha_entrega_real = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Entrega Real')
    fecha_devolucion_real = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Devolución Real')

    # Estado
    estado = models.CharField(
        max_length=20,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE,
        verbose_name='Estado'
    )

    # Costos
    costo_alquiler = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo de Alquiler'
    )
    deposito_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Depósito Pagado'
    )
    costo_adicional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cargos por daños, retrasos, etc.",
        verbose_name='Costo Adicional'
    )

    # Notas
    notas_cliente = models.TextField(blank=True, verbose_name='Notas del Cliente')
    notas_admin = models.TextField(blank=True, verbose_name='Notas del Administrador')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmada_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmada el')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['equipo', 'fecha_inicio', 'fecha_fin']),
            models.Index(fields=['numero_reserva']),
        ]

    def __str__(self):
        return f"Reserva {self.numero_reserva} - {self.equipo.nombre}"

    def save(self, *args, **kwargs):
        if not self.numero_reserva:
            # Generar número de reserva único
            self.numero_reserva = 'RES-' + ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
        super().save(*args, **kwargs)

    def calcular_costo(self):
        """Calcula el costo total de la reserva"""
        self.costo_alquiler = self.equipo.calcular_precio(
            self.fecha_inicio,
            self.fecha_fin
        )
        self.save(update_fields=['costo_alquiler'])
        return self.costo_alquiler

    @property
    def costo_total(self):
        """Retorna el costo total incluyendo adicionales"""
        return self.costo_alquiler + self.costo_adicional

    @property
    def dias_alquiler(self):
        """Retorna la cantidad de días del alquiler"""
        return (self.fecha_fin - self.fecha_inicio).days

    def confirmar_reserva(self):
        """Confirma la reserva y marca el equipo como rentado"""
        from django.utils import timezone

        if self.estado != self.EstadoReserva.PENDIENTE:
            raise ValueError("Solo se pueden confirmar reservas pendientes")

        # Verificar disponibilidad
        if not self.equipo.consultar_disponibilidad(self.fecha_inicio, self.fecha_fin):
            raise ValueError("El equipo no está disponible para estas fechas")

        self.estado = self.EstadoReserva.CONFIRMADA
        self.confirmada_at = timezone.now()
        self.save()

        # Marcar equipo como rentado si la fecha de inicio es hoy
        if self.fecha_inicio <= timezone.now().date():
            self.equipo.marcar_como_rentado()

    def iniciar_alquiler(self):
        """Inicia el alquiler (entrega del equipo)"""
        from django.utils import timezone

        if self.estado != self.EstadoReserva.CONFIRMADA:
            raise ValueError("Solo se pueden iniciar reservas confirmadas")

        self.estado = self.EstadoReserva.EN_CURSO
        self.fecha_entrega_real = timezone.now()
        self.save()

        self.equipo.marcar_como_rentado()

    def completar_alquiler(self):
        """Completa el alquiler (devolución del equipo)"""
        from django.utils import timezone

        if self.estado != self.EstadoReserva.EN_CURSO:
            raise ValueError("Solo se pueden completar reservas en curso")

        self.estado = self.EstadoReserva.COMPLETADA
        self.fecha_devolucion_real = timezone.now()
        self.save()

        self.equipo.marcar_como_disponible()

        # Verificar si hay retraso
        if self.fecha_devolucion_real.date() > self.fecha_fin:
            dias_retraso = (self.fecha_devolucion_real.date() - self.fecha_fin).days
            # Aplicar cargo por retraso (50% del precio diario)
            cargo_retraso = self.equipo.precio_por_dia * Decimal('0.5') * dias_retraso
            self.costo_adicional += cargo_retraso
            self.save(update_fields=['costo_adicional'])

    def cancelar_reserva(self):
        """Cancela la reserva"""
        if self.estado in [self.EstadoReserva.COMPLETADA, self.EstadoReserva.CANCELADA]:
            raise ValueError("No se puede cancelar una reserva completada o ya cancelada")

        self.estado = self.EstadoReserva.CANCELADA
        self.save()

        # Si el equipo estaba rentado, marcarlo como disponible
        if self.equipo.estado == self.equipo.EstadoEquipo.RENTADO:
            self.equipo.marcar_como_disponible()
