from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Usuario(AbstractUser):
    """Usuario del sistema con roles"""

    class TipoUsuario(models.TextChoices):
        CLIENTE = 'cliente', 'Cliente'
        ADMINISTRADOR = 'administrador', 'Administrador'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.CLIENTE,
        verbose_name='Tipo de Usuario'
    )

    # Campos adicionales
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    codigo_postal = models.CharField(max_length=10, blank=True, verbose_name='Código Postal')

    # Verificación
    email_verificado = models.BooleanField(default=False, verbose_name='Email Verificado')
    telefono_verificado = models.BooleanField(default=False, verbose_name='Teléfono Verificado')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_tipo_usuario_display()})"

    @property
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.tipo_usuario == self.TipoUsuario.ADMINISTRADOR

    @property
    def es_cliente(self):
        """Verifica si el usuario es cliente"""
        return self.tipo_usuario == self.TipoUsuario.CLIENTE

    def puede_gestionar_equipos(self):
        """Verifica si puede gestionar equipos"""
        return self.es_administrador

    def puede_realizar_reservas(self):
        """Verifica si puede realizar reservas"""
        return self.es_cliente or self.es_administrador
