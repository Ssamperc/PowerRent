from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from reservas.models import Reserva
from .models import Pago
from .services import PagoService


class MisPagosView(LoginRequiredMixin, ListView):
    model = Pago
    template_name = 'pagos/mis_pagos.html'
    context_object_name = 'pagos'
    paginate_by = 10

    def get_queryset(self):
        return Pago.objects.filter(
            usuario=self.request.user
        ).select_related('reserva', 'reserva__equipo').order_by('-created_at')


class DetallePagoView(LoginRequiredMixin, DetailView):
    model = Pago
    template_name = 'pagos/detalle.html'
    context_object_name = 'pago'

    def get_queryset(self):
        if self.request.user.es_administrador:
            return Pago.objects.all()
        return Pago.objects.filter(usuario=self.request.user)


class PagarReservaView(LoginRequiredMixin, DetailView):
    model = Reserva
    template_name = 'pagos/pagar.html'
    context_object_name = 'reserva'

    def get_queryset(self):
        return Reserva.objects.filter(
            cliente=self.request.user,
            estado=Reserva.EstadoReserva.PENDIENTE
        )

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        metodo_pago = request.POST.get('metodo_pago')

        if metodo_pago not in [m.value for m in Pago.MetodoPago]:
            messages.error(request, 'Método de pago inválido.')
            return redirect('pagos:pagar', pk=reserva.pk)

        try:
            resultados = PagoService.procesar_pago_completo(
                reserva=reserva,
                usuario=request.user,
                metodo_pago=metodo_pago
            )

            if resultados.get('reserva_confirmada'):
                messages.success(
                    request,
                    f'Pago procesado exitosamente. Reserva {reserva.numero_reserva} confirmada.'
                )
            else:
                messages.warning(request, 'Pago procesado pero hubo un problema al confirmar la reserva.')

            return redirect('reservas:detalle', pk=reserva.pk)

        except Exception as e:
            messages.error(request, f'Error procesando el pago: {e}')
            return redirect('pagos:pagar', pk=reserva.pk)
