from django.urls import path
from . import views

app_name = 'equipos'

urlpatterns = [
    path('', views.ListaEquiposView.as_view(), name='lista'),
    path('categoria/<slug:slug>/', views.EquiposPorCategoriaView.as_view(), name='por_categoria'),
    path('<slug:slug>/calificar/', views.CalificarEquipoView.as_view(), name='calificar'),
    path('<slug:slug>/', views.DetalleEquipoView.as_view(), name='detalle'),
]
