from django.urls import path
from . import views
from .webhooks import StripeWebhookView, PayPalWebhookView

app_name = 'pagos'

urlpatterns = [
    path('', views.MisPagosView.as_view(), name='mis_pagos'),
    path('<uuid:pk>/', views.DetallePagoView.as_view(), name='detalle'),
    path('reserva/<uuid:pk>/pagar/', views.PagarReservaView.as_view(), name='pagar'),
    # Webhooks de pasarelas de pago
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='webhook_stripe'),
    path('webhooks/paypal/', PayPalWebhookView.as_view(), name='webhook_paypal'),
]
