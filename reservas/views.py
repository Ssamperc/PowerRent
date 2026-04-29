from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from equipos.models import Equipo
from .models import Reserva
from .forms import ReservaForm
from .services import ReservaService


class MisReservasView(LoginRequiredMixin, ListView):
    model = Reserva
    template_name = 'reservas/mis_reservas.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        return Reserva.objects.filter(
            cliente=self.request.user
        ).select_related('equipo', 'equipo__categoria').order_by('-created_at')


class DetalleReservaView(LoginRequiredMixin, DetailView):
    model = Reserva
    template_name = 'reservas/detalle.html'
    context_object_name = 'reserva'

    def get_queryset(self):
        if self.request.user.es_administrador:
            return Reserva.objects.all()
        return Reserva.objects.filter(cliente=self.request.user)


class CrearReservaView(LoginRequiredMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/crear.html'

    def dispatch(self, request, *args, **kwargs):
        self.equipo = get_object_or_404(Equipo, slug=kwargs['equipo_slug'], activo=True)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.equipo
        return context

    def form_valid(self, form):
        try:
            reserva = ReservaService.crear_reserva(
                cliente=self.request.user,
                equipo=self.equipo,
                fecha_inicio=form.cleaned_data['fecha_inicio'],
                fecha_fin=form.cleaned_data['fecha_fin'],
                notas=form.cleaned_data.get('notas_cliente', '')
            )
            messages.success(
                self.request,
                f'Reserva {reserva.numero_reserva} creada exitosamente. Costo: ${reserva.costo_alquiler:,.0f}'
            )
            return redirect('reservas:detalle', pk=reserva.pk)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class CancelarReservaView(LoginRequiredMixin, DetailView):
    model = Reserva
    template_name = 'reservas/cancelar.html'
    context_object_name = 'reserva'

    def get_queryset(self):
        return Reserva.objects.filter(cliente=self.request.user)

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        try:
            reserva.cancelar_reserva()
            messages.success(request, f'Reserva {reserva.numero_reserva} cancelada exitosamente.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('reservas:mis_reservas')
