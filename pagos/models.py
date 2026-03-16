from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import random
import string


class Pago(models.Model):
    """Pago de una reserva"""

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        TARJETA_CREDITO = 'tarjeta_credito', 'Tarjeta de Crédito'
        TARJETA_DEBITO = 'tarjeta_debito', 'Tarjeta de Débito'
        TRANSFERENCIA = 'transferencia', 'Transferencia Bancaria'
        PAYPAL = 'paypal', 'PayPal'
        STRIPE = 'stripe', 'Stripe'

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PROCESANDO = 'procesando', 'Procesando'
        COMPLETADO = 'completado', 'Completado'
        FALLIDO = 'fallido', 'Fallido'
        REEMBOLSADO = 'reembolsado', 'Reembolsado'

    class TipoPago(models.TextChoices):
        ALQUILER = 'alquiler', 'Pago de Alquiler'
        DEPOSITO = 'deposito', 'Depósito de Garantía'
        ADICIONAL = 'adicional', 'Cargo Adicional'
        REEMBOLSO = 'reembolso', 'Reembolso'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_transaccion = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='Número de Transacción'
    )

    # Relaciones
    reserva = models.ForeignKey(
        'reservas.Reserva',
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Reserva'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Usuario'
    )

    # Información del pago
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    tipo_pago = models.CharField(
        max_length=20,
        choices=TipoPago.choices,
        default=TipoPago.ALQUILER,
        verbose_name='Tipo de Pago'
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        verbose_name='Método de Pago'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE,
        verbose_name='Estado'
    )

    # Fechas
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Pago')
    fecha_procesado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Procesado')

    # Referencia externa (pasarela de pago)
    referencia_externa = models.CharField(
        max_length=200,
        blank=True,
        help_text="ID de transacción del procesador de pagos",
        verbose_name='Referencia Externa'
    )

    # Notas
    notas = models.TextField(blank=True, verbose_name='Notas')

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['reserva', 'estado']),
            models.Index(fields=['usuario', 'fecha_pago']),
            models.Index(fields=['numero_transaccion']),
        ]

    def __str__(self):
        return f"Pago {self.numero_transaccion} - ${self.monto}"

    def save(self, *args, **kwargs):
        if not self.numero_transaccion:
            self.numero_transaccion = 'PAY-' + ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=12)
            )
        super().save(*args, **kwargs)

    def procesar_pago(self):
        """
        Procesa el pago según el método seleccionado

        Returns:
            bool: True si el pago fue exitoso
        """
        from django.utils import timezone

        if self.estado != self.EstadoPago.PENDIENTE:
            raise ValueError("Solo se pueden procesar pagos pendientes")

        self.estado = self.EstadoPago.PROCESANDO
        self.save()

        try:
            if self.metodo_pago == self.MetodoPago.STRIPE:
                resultado = self._procesar_con_stripe()
            elif self.metodo_pago == self.MetodoPago.PAYPAL:
                resultado = self._procesar_con_paypal()
            else:
                # Pagos manuales (efectivo, transferencia, tarjeta presencial)
                resultado = True

            if resultado:
                self.estado = self.EstadoPago.COMPLETADO
                self.fecha_procesado = timezone.now()
                self.save()
                return True
            else:
                self.estado = self.EstadoPago.FALLIDO
                self.save()
                return False

        except Exception as e:
            self.estado = self.EstadoPago.FALLIDO
            self.notas = f"Error: {str(e)}"
            self.save()
            return False

    def _procesar_con_stripe(self):
        """
        Procesa pago con Stripe.
        En producción se integraría con la API de Stripe.
        """
        # Aquí iría: stripe.PaymentIntent.create(amount=..., currency='cop', ...)
        return True

    def _procesar_con_paypal(self):
        """
        Procesa pago con PayPal.
        En producción se integraría con la API de PayPal.
        """
        # Aquí iría la integración con PayPal SDK
        return True

    def reembolsar(self, motivo=''):
        """
        Reembolsa el pago y crea un registro de reembolso

        Args:
            motivo: Motivo del reembolso

        Returns:
            Pago: El pago de reembolso creado
        """
        if self.estado != self.EstadoPago.COMPLETADO:
            raise ValueError("Solo se pueden reembolsar pagos completados")

        # Crear registro de reembolso
        pago_reembolso = Pago.objects.create(
            reserva=self.reserva,
            usuario=self.usuario,
            monto=self.monto,
            tipo_pago=self.TipoPago.REEMBOLSO,
            metodo_pago=self.metodo_pago,
            estado=self.EstadoPago.COMPLETADO,
            notas=f"Reembolso de {self.numero_transaccion}. {motivo}"
        )

        self.estado = self.EstadoPago.REEMBOLSADO
        if motivo:
            self.notas += f"\nReembolsado: {motivo}"
        self.save()

        return pago_reembolso

    @property
    def es_completado(self):
        return self.estado == self.EstadoPago.COMPLETADO

    @property
    def es_pendiente(self):
        return self.estado == self.EstadoPago.PENDIENTE
