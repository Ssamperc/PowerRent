"""
Vista de reportes usando Inversión de Dependencias.
El controlador depende de la interfaz IReporteGenerator,
no de implementaciones concretas.
"""
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from equipos.models import Equipo
from .reportes import get_reporte_generator


class ReporteEquiposView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Genera reporte de equipos en PDF o Excel/CSV.
    Implementa Inversión de Dependencias: el controlador usa la interfaz
    IReporteGenerator sin conocer la implementación concreta.
    """

    def test_func(self):
        return self.request.user.es_administrador

    def get(self, request):
        formato = request.GET.get('formato', 'excel')
        estado = request.GET.get('estado', 'todos')

        # Filtrar equipos según estado
        equipos = Equipo.objects.select_related('categoria').filter(activo=True)
        if estado == 'disponibles':
            equipos = equipos.filter(disponible=True)
        elif estado == 'no_disponibles':
            equipos = equipos.filter(disponible=False)

        # Inyección de dependencia: obtenemos la implementación correcta
        # sin que este controlador conozca los detalles concretos
        generador = get_reporte_generator(formato)

        titulo = f'Reporte de Equipos PowerRent - {estado.title()}'
        contenido = generador.generar(equipos, titulo)

        response = HttpResponse(contenido, content_type=generador.content_type())
        response['Content-Disposition'] = (
            f'attachment; filename="reporte_equipos.{generador.extension()}"'
        )
        return response
