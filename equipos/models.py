from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Categoria(models.Model):
    """Categoría de equipos"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True, verbose_name='Imagen')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden de visualización')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    @property
    def total_equipos(self):
        """Retorna el total de equipos en esta categoría"""
        return self.equipos.filter(activo=True).count()

    @property
    def equipos_disponibles(self):
        """Retorna equipos disponibles en esta categoría"""
        return self.equipos.filter(activo=True, disponible=True).count()


class Equipo(models.Model):
    """Equipo disponible para alquiler"""

    class EstadoEquipo(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        RENTADO = 'rentado', 'Rentado'
        MANTENIMIENTO = 'mantenimiento', 'En Mantenimiento'
        FUERA_SERVICIO = 'fuera_servicio', 'Fuera de Servicio'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Información básica
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    descripcion = models.TextField(verbose_name='Descripción')

    # Categoría
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='equipos',
        verbose_name='Categoría'
    )

    # Identificación
    codigo_interno = models.CharField(
        max_length=50, unique=True,
        help_text="Código único del equipo",
        verbose_name='Código Interno'
    )
    marca = models.CharField(max_length=100, blank=True, verbose_name='Marca')
    modelo = models.CharField(max_length=100, blank=True, verbose_name='Modelo')
    numero_serie = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name='Número de Serie')

    # Precios (DecimalField obligatorio para dinero, nunca float/double)
    precio_por_dia = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio por Día'
    )
    precio_por_semana = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Precio especial por semana (7 días)",
        verbose_name='Precio por Semana'
    )
    precio_por_mes = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Precio especial por mes (30 días)",
        verbose_name='Precio por Mes'
    )

    # Depósito de garantía
    deposito_garantia = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Depósito requerido para alquilar el equipo",
        verbose_name='Depósito de Garantía'
    )

    # Estado y disponibilidad
    estado = models.CharField(
        max_length=20, choices=EstadoEquipo.choices,
        default=EstadoEquipo.DISPONIBLE, verbose_name='Estado'
    )
    disponible = models.BooleanField(default=True, verbose_name='Disponible')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    # Especificaciones técnicas (JSONField para datos flexibles)
    especificaciones = models.JSONField(
        default=dict, blank=True,
        help_text="Especificaciones técnicas del equipo",
        verbose_name='Especificaciones Técnicas'
    )

    # Imagen principal
    imagen_principal = models.ImageField(
        upload_to='equipos/%Y/%m/', null=True, blank=True,
        verbose_name='Imagen Principal'
    )

    # Mantenimiento
    ultima_fecha_mantenimiento = models.DateField(null=True, blank=True, verbose_name='Última Fecha de Mantenimiento')
    proxima_fecha_mantenimiento = models.DateField(null=True, blank=True, verbose_name='Próxima Fecha de Mantenimiento')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['categoria', 'disponible']),
            models.Index(fields=['codigo_interno']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_interno})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.nombre}-{self.codigo_interno}")
        super().save(*args, **kwargs)

    def consultar_disponibilidad(self, fecha_inicio, fecha_fin):
        """
        Verifica si el equipo está disponible en un rango de fechas.
        Considera reservas activas Y bloqueos de disponibilidad.

        Args:
            fecha_inicio: Fecha de inicio de la reserva
            fecha_fin: Fecha de fin de la reserva

        Returns:
            bool: True si está disponible, False si no
        """
        if not self.disponible or not self.activo:
            return False

        if self.estado != self.EstadoEquipo.DISPONIBLE:
            return False

        from reservas.models import Reserva

        # Verificar reservas solapadas
        reservas_solapadas = self.reservas.filter(
            estado__in=[Reserva.EstadoReserva.CONFIRMADA, Reserva.EstadoReserva.EN_CURSO],
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio
        ).exists()

        if reservas_solapadas:
            return False

        # Verificar bloqueos de disponibilidad
        bloqueos = self.bloqueos.filter(
            activo=True,
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio
        ).exists()

        return not bloqueos

    def calcular_precio(self, fecha_inicio, fecha_fin):
        """
        Calcula el precio total del alquiler según las fechas.
        Aplica precios especiales si se configuraron semana/mes.

        Returns:
            Decimal: Precio total
        """
        dias = (fecha_fin - fecha_inicio).days

        if dias <= 0:
            return Decimal('0.00')

        if dias >= 30 and self.precio_por_mes:
            meses = dias // 30
            dias_restantes = dias % 30
            total = (self.precio_por_mes * meses) + (self.precio_por_dia * dias_restantes)
        elif dias >= 7 and self.precio_por_semana:
            semanas = dias // 7
            dias_restantes = dias % 7
            total = (self.precio_por_semana * semanas) + (self.precio_por_dia * dias_restantes)
        else:
            total = self.precio_por_dia * dias

        return total

    def marcar_como_rentado(self):
        """Marca el equipo como rentado"""
        self.estado = self.EstadoEquipo.RENTADO
        self.disponible = False
        self.save(update_fields=['estado', 'disponible', 'updated_at'])

    def marcar_como_disponible(self):
        """Marca el equipo como disponible"""
        self.estado = self.EstadoEquipo.DISPONIBLE
        self.disponible = True
        self.save(update_fields=['estado', 'disponible', 'updated_at'])

    def enviar_a_mantenimiento(self, motivo=''):
        """Envía el equipo a mantenimiento"""
        self.estado = self.EstadoEquipo.MANTENIMIENTO
        self.disponible = False
        self.save(update_fields=['estado', 'disponible', 'updated_at'])

    def requiere_mantenimiento(self):
        """Verifica si el equipo requiere mantenimiento"""
        from django.utils import timezone

        if not self.proxima_fecha_mantenimiento:
            return False

        return timezone.now().date() >= self.proxima_fecha_mantenimiento


class ImagenEquipo(models.Model):
    """Imágenes adicionales del equipo"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipo = models.ForeignKey(
        Equipo, on_delete=models.CASCADE,
        related_name='imagenes', verbose_name='Equipo'
    )
    imagen = models.ImageField(upload_to='equipos/%Y/%m/', verbose_name='Imagen')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen de Equipo'
        verbose_name_plural = 'Imágenes de Equipos'
        ordering = ['orden', 'created_at']

    def __str__(self):
        return f"Imagen de {self.equipo.nombre}"


class BloqueoDisponibilidad(models.Model):
    """
    Bloquea la disponibilidad de un equipo por mantenimiento u otras razones.
    Esto evita que los clientes puedan reservar el equipo en esas fechas.
    """

    class MotivoBloqueo(models.TextChoices):
        MANTENIMIENTO = 'mantenimiento', 'Mantenimiento Programado'
        REPARACION = 'reparacion', 'Reparación'
        RESERVADO_ADMIN = 'reservado_admin', 'Reservado por Administración'
        INSPECCION = 'inspeccion', 'Inspección Técnica'
        OTRO = 'otro', 'Otro'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipo = models.ForeignKey(
        Equipo, on_delete=models.CASCADE,
        related_name='bloqueos', verbose_name='Equipo'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    tipo_motivo = models.CharField(
        max_length=20, choices=MotivoBloqueo.choices,
        default=MotivoBloqueo.MANTENIMIENTO, verbose_name='Motivo'
    )
    motivo = models.CharField(max_length=300, verbose_name='Descripción del Motivo')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bloqueos_creados',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bloqueo de Disponibilidad'
        verbose_name_plural = 'Bloqueos de Disponibilidad'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Bloqueo {self.equipo.nombre}: {self.fecha_inicio} → {self.fecha_fin} ({self.motivo})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')


class CalificacionEquipo(models.Model):
    """
    Calificación y reseña de un equipo por parte del cliente.
    Los clientes pueden calificar equipos que han alquilado.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipo = models.ForeignKey(
        Equipo, on_delete=models.CASCADE,
        related_name='calificaciones', verbose_name='Equipo'
    )
    cliente = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.CASCADE,
        related_name='calificaciones', verbose_name='Cliente'
    )
    reserva = models.OneToOneField(
        'reservas.Reserva', on_delete=models.CASCADE,
        related_name='calificacion', verbose_name='Reserva'
    )
    puntuacion = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} estrellas') for i in range(1, 6)],
        verbose_name='Puntuación (1-5)'
    )
    comentario = models.TextField(blank=True, verbose_name='Comentario')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        ordering = ['-created_at']
        unique_together = [('equipo', 'cliente', 'reserva')]

    def __str__(self):
        return f"{self.puntuacion}⭐ - {self.equipo.nombre} por {self.cliente.username}"
