from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from .models import Equipo, Categoria, CalificacionEquipo
from .forms import CalificacionForm
from .filters import EquipoFilter
from .services import EquipoService


class ListaEquiposView(ListView):
    model = Equipo
    template_name = 'equipos/lista.html'
    context_object_name = 'equipos'
    paginate_by = 12

    def get_queryset(self):
        queryset = Equipo.objects.filter(
            activo=True
        ).select_related('categoria').prefetch_related('imagenes')
        self.filtro = EquipoFilter(self.request.GET, queryset=queryset)
        return self.filtro.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro'] = self.filtro
        context['categorias'] = Categoria.objects.filter(activo=True)
        return context


class DetalleEquipoView(DetailView):
    model = Equipo
    template_name = 'equipos/detalle.html'
    context_object_name = 'equipo'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Equipo.objects.filter(activo=True).select_related('categoria').prefetch_related('imagenes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipos_relacionados'] = Equipo.objects.filter(
            categoria=self.object.categoria,
            activo=True,
            disponible=True
        ).exclude(pk=self.object.pk)[:4]
        context['calificaciones'] = self.object.calificaciones.select_related('cliente').order_by('-created_at')[:10]
        # Check if current user can rate this equipment
        context['puede_calificar'] = False
        if self.request.user.is_authenticated:
            from reservas.models import Reserva
            reserva_completada = Reserva.objects.filter(
                cliente=self.request.user,
                equipo=self.object,
                estado=Reserva.EstadoReserva.COMPLETADA
            ).exclude(calificacion__isnull=False).first()
            context['puede_calificar'] = reserva_completada is not None
            context['reserva_para_calificar'] = reserva_completada
        return context


class EquiposPorCategoriaView(ListView):
    model = Equipo
    template_name = 'equipos/por_categoria.html'
    context_object_name = 'equipos'
    paginate_by = 12

    def get_queryset(self):
        self.categoria = Categoria.objects.get(slug=self.kwargs['slug'], activo=True)
        return Equipo.objects.filter(
            categoria=self.categoria,
            activo=True
        ).select_related('categoria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.categoria
        context['categorias'] = Categoria.objects.filter(activo=True)
        return context


class CalificarEquipoView(LoginRequiredMixin, CreateView):
    """Permite a un cliente calificar un equipo que alquiló."""
    model = CalificacionEquipo
    form_class = CalificacionForm
    template_name = 'equipos/calificar.html'

    def dispatch(self, request, *args, **kwargs):
        self.equipo = get_object_or_404(Equipo, slug=self.kwargs['slug'], activo=True)
        if request.user.is_authenticated:
            from reservas.models import Reserva
            self.reserva = Reserva.objects.filter(
                cliente=request.user,
                equipo=self.equipo,
                estado=Reserva.EstadoReserva.COMPLETADA
            ).exclude(calificacion__isnull=False).first()
            if not self.reserva:
                messages.warning(request, 'Solo puedes calificar equipos que hayas alquilado y devuelto.')
                return redirect('equipos:detalle', slug=self.equipo.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['equipo'] = self.equipo
        return ctx

    def form_valid(self, form):
        form.instance.equipo = self.equipo
        form.instance.cliente = self.request.user
        form.instance.reserva = self.reserva
        response = super().form_valid(form)
        try:
            from core.notificaciones import NotificacionService
            NotificacionService.nueva_calificacion(form.instance)
        except Exception:
            pass
        messages.success(self.request, f'¡Gracias por calificar "{self.equipo.nombre}"!')
        return response

    def get_success_url(self):
        return reverse('equipos:detalle', kwargs={'slug': self.equipo.slug})
