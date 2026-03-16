"""
Webhooks para procesadores de pago externos.

Los webhooks reciben notificaciones en tiempo real de Stripe/PayPal
cuando ocurre un evento (pago completado, reembolso, disputa, etc.).

URLs de webhook (agregar en settings de cada plataforma):
  • Stripe:  https://tudominio.com/pagos/webhooks/stripe/
  • PayPal:  https://tudominio.com/pagos/webhooks/paypal/

Para verificar webhooks de Stripe en desarrollo:
  stripe listen --forward-to localhost:8000/pagos/webhooks/stripe/
"""

import json
import logging
import hashlib
import hmac

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from .models import Pago

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Webhook para eventos de Stripe.
    Verifica la firma del webhook para garantizar autenticidad.
    """

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        # Verificar firma del webhook
        if webhook_secret and not self._verificar_firma_stripe(payload, sig_header, webhook_secret):
            logger.warning("Webhook de Stripe con firma inválida")
            return HttpResponse(status=400)

        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        event_type = event.get('type')
        logger.info(f"Webhook Stripe recibido: {event_type}")

        # Manejar eventos de Stripe
        handlers = {
            'payment_intent.succeeded': self._handle_payment_succeeded,
            'payment_intent.payment_failed': self._handle_payment_failed,
            'charge.refunded': self._handle_refund,
            'charge.dispute.created': self._handle_dispute,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                handler(event['data']['object'])
            except Exception as e:
                logger.error(f"Error procesando webhook Stripe {event_type}: {e}")
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'received': True})

    def _verificar_firma_stripe(self, payload, sig_header, secret):
        """Verifica la firma HMAC del webhook de Stripe"""
        try:
            timestamp, signature = sig_header.split(',')
            timestamp = timestamp.split('=')[1]
            signature = signature.split('=')[1]

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected, signature)
        except Exception:
            return False

    def _handle_payment_succeeded(self, payment_intent):
        """Maneja pago exitoso de Stripe"""
        referencia = payment_intent.get('id', '')

        try:
            pago = Pago.objects.get(referencia_externa=referencia)
            if pago.estado != Pago.EstadoPago.COMPLETADO:
                pago.estado = Pago.EstadoPago.COMPLETADO
                pago.fecha_procesado = timezone.now()
                pago.save()

                # Confirmar reserva si el pago es del alquiler
                if pago.tipo_pago == Pago.TipoPago.ALQUILER:
                    try:
                        pago.reserva.confirmar_reserva()
                    except ValueError as e:
                        logger.warning(f"No se pudo confirmar reserva: {e}")

                logger.info(f"Pago {pago.numero_transaccion} marcado como completado via Stripe")
        except Pago.DoesNotExist:
            logger.warning(f"Pago con referencia Stripe {referencia} no encontrado")

    def _handle_payment_failed(self, payment_intent):
        """Maneja pago fallido de Stripe"""
        referencia = payment_intent.get('id', '')

        try:
            pago = Pago.objects.get(referencia_externa=referencia)
            pago.estado = Pago.EstadoPago.FALLIDO
            pago.notas = f"Stripe: {payment_intent.get('last_payment_error', {}).get('message', 'Error desconocido')}"
            pago.save()
            logger.warning(f"Pago {pago.numero_transaccion} falló en Stripe")
        except Pago.DoesNotExist:
            logger.warning(f"Pago con referencia Stripe {referencia} no encontrado")

    def _handle_refund(self, charge):
        """Maneja reembolso de Stripe"""
        referencia = charge.get('payment_intent', '')
        logger.info(f"Reembolso de Stripe para: {referencia}")

        try:
            pago = Pago.objects.get(referencia_externa=referencia)
            pago.estado = Pago.EstadoPago.REEMBOLSADO
            pago.save()
        except Pago.DoesNotExist:
            pass

    def _handle_dispute(self, dispute):
        """Maneja disputa/contracargo de Stripe"""
        logger.error(f"Disputa Stripe: {dispute.get('id')} - ${dispute.get('amount', 0) / 100}")


@method_decorator(csrf_exempt, name='dispatch')
class PayPalWebhookView(View):
    """
    Webhook para eventos de PayPal.
    """

    def post(self, request, *args, **kwargs):
        try:
            event = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        event_type = event.get('event_type')
        logger.info(f"Webhook PayPal recibido: {event_type}")

        handlers = {
            'PAYMENT.CAPTURE.COMPLETED': self._handle_payment_completed,
            'PAYMENT.CAPTURE.DENIED': self._handle_payment_denied,
            'PAYMENT.CAPTURE.REFUNDED': self._handle_refund,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                handler(event.get('resource', {}))
            except Exception as e:
                logger.error(f"Error procesando webhook PayPal {event_type}: {e}")

        return JsonResponse({'received': True})

    def _handle_payment_completed(self, resource):
        """Maneja pago completado de PayPal"""
        referencia = resource.get('id', '')

        try:
            pago = Pago.objects.get(referencia_externa=referencia)
            pago.estado = Pago.EstadoPago.COMPLETADO
            pago.fecha_procesado = timezone.now()
            pago.save()
            logger.info(f"Pago PayPal completado: {pago.numero_transaccion}")
        except Pago.DoesNotExist:
            logger.warning(f"Pago PayPal {referencia} no encontrado")

    def _handle_payment_denied(self, resource):
        """Maneja pago denegado de PayPal"""
        referencia = resource.get('id', '')

        try:
            pago = Pago.objects.get(referencia_externa=referencia)
            pago.estado = Pago.EstadoPago.FALLIDO
            pago.notas = "PayPal: Pago denegado"
            pago.save()
        except Pago.DoesNotExist:
            pass

    def _handle_refund(self, resource):
        """Maneja reembolso de PayPal"""
        referencia = resource.get('id', '')
        logger.info(f"Reembolso PayPal: {referencia}")
