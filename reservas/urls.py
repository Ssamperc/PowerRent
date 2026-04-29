from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.MisReservasView.as_view(), name='mis_reservas'),
    path('nueva/<slug:equipo_slug>/', views.CrearReservaView.as_view(), name='crear'),
    path('<uuid:pk>/', views.DetalleReservaView.as_view(), name='detalle'),
    path('<uuid:pk>/cancelar/', views.CancelarReservaView.as_view(), name='cancelar'),
]
