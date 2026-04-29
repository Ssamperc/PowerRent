import uuid
from django.db import models
from django.conf import settings


class TimestampMixin(models.Model):
    """Mixin que agrega campos de auditoría a los modelos"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    """Mixin que usa UUID como primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Notificacion(models.Model):
    """Notificación interna del sistema para usuarios."""

    class Tipo(models.TextChoices):
        RESERVA_CREADA = 'reserva_creada', 'Nueva Reserva Creada'
        RESERVA_CONFIRMADA = 'reserva_confirmada', 'Reserva Confirmada'
        RESERVA_CANCELADA = 'reserva_cancelada', 'Reserva Cancelada'
        RESERVA_EN_CURSO = 'reserva_en_curso', 'Alquiler Iniciado'
        RESERVA_COMPLETADA = 'reserva_completada', 'Alquiler Completado'
        PAGO_RECIBIDO = 'pago_recibido', 'Pago Recibido'
        RECORDATORIO_ENTREGA = 'recordatorio_entrega', 'Recordatorio de Entrega'
        RECORDATORIO_DEVOLUCION = 'recordatorio_devolucion', 'Recordatorio de Devolución'
        NUEVA_CALIFICACION = 'nueva_calificacion', 'Nueva Calificación'
        ADMIN_NUEVA_RESERVA = 'admin_nueva_reserva', 'Nueva Reserva (Admin)'
        ADMIN_NUEVO_USUARIO = 'admin_nuevo_usuario', 'Nuevo Usuario Registrado'

    ICONOS = {
        'reserva_creada': 'bi-calendar-plus text-primary',
        'reserva_confirmada': 'bi-calendar-check text-success',
        'reserva_cancelada': 'bi-calendar-x text-danger',
        'reserva_en_curso': 'bi-play-circle text-success',
        'reserva_completada': 'bi-check-circle text-secondary',
        'pago_recibido': 'bi-credit-card text-success',
        'recordatorio_entrega': 'bi-alarm text-warning',
        'recordatorio_devolucion': 'bi-alarm text-danger',
        'nueva_calificacion': 'bi-star text-warning',
        'admin_nueva_reserva': 'bi-bell text-primary',
        'admin_nuevo_usuario': 'bi-person-plus text-info',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices, verbose_name='Tipo')
    titulo = models.CharField(max_length=200, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    url = models.CharField(max_length=500, blank=True, verbose_name='URL')
    leida = models.BooleanField(default=False, verbose_name='Leída')
    leida_at = models.DateTimeField(null=True, blank=True, verbose_name='Leída el')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['usuario', 'created_at']),
        ]

    def __str__(self):
        return f"{self.titulo} → {self.usuario.username}"

    @property
    def icono_css(self):
        return self.ICONOS.get(self.tipo, 'bi-bell text-muted')

    def marcar_leida(self):
        from django.utils import timezone
        if not self.leida:
            self.leida = True
            self.leida_at = timezone.now()
            self.save(update_fields=['leida', 'leida_at'])
