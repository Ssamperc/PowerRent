from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count
from equipos.models import Equipo, Categoria
from reservas.services import ReservaService


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipos_destacados'] = Equipo.objects.filter(
            activo=True, disponible=True
        ).select_related('categoria').order_by('-created_at')[:6]
        context['categorias'] = Categoria.objects.filter(activo=True)[:8]
        context['total_equipos'] = Equipo.objects.filter(activo=True).count()
        return context


class SobreNosotrosView(TemplateView):
    template_name = 'sobre_nosotros.html'


class DashboardAdminView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard de administrador con estadísticas del sistema.
    Solo accesible para usuarios con tipo_usuario='administrador'.
    """
    template_name = 'dashboard_admin.html'

    def test_func(self):
        return self.request.user.es_administrador

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(ReservaService.obtener_estadisticas())
        return context


class AliadosView(TemplateView):
    """
    Vista que consume el servicio JSON del equipo aliado
    y muestra sus productos en PowerRent.
    """
    template_name = 'aliados.html'

    def get_context_data(self, **kwargs):
        from .servicios_externos import consumir_servicio_aliado
        context = super().get_context_data(**kwargs)
        context['aliados_data'] = consumir_servicio_aliado()
        return context
