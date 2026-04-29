from django.urls import path
from . import api_views

urlpatterns = [
    path('equipos/', api_views.EquiposDisponiblesAPIView.as_view(), name='api_equipos'),
    path('equipos/<slug:slug>/', api_views.EquipoDetalleAPIView.as_view(), name='api_equipo_detalle'),
    path('aliados/', api_views.ServicioAliadosAPIView.as_view(), name='api_aliados'),
]
