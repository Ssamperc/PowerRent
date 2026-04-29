from django.urls import path
from . import views
from . import gestion_views
from . import notificaciones_views
from . import reporte_views

app_name = 'core'

urlpatterns = [
    # ─── Páginas públicas ─────────────────────────────────
    path('', views.HomeView.as_view(), name='home'),
    path('sobre-nosotros/', views.SobreNosotrosView.as_view(), name='sobre_nosotros'),
    path('dashboard/', views.DashboardAdminView.as_view(), name='dashboard_admin'),

    # ─── Notificaciones ──────────────────────────────────
    path('notificaciones/', notificaciones_views.NotificacionesListView.as_view(), name='notificaciones'),
    path('notificaciones/<uuid:pk>/leer/', notificaciones_views.MarcarLeidaView.as_view(), name='notificacion_leer'),
    path('notificaciones/leer-todas/', notificaciones_views.MarcarTodasLeidasView.as_view(), name='notificaciones_leer_todas'),

    # ─── Gestión: Equipos ────────────────────────────────
    path('gestion/', gestion_views.GestionInicioView.as_view(), name='gestion_inicio'),
    path('gestion/equipos/', gestion_views.GestionEquiposListView.as_view(), name='gestion_equipos'),
    path('gestion/equipos/nuevo/', gestion_views.GestionEquipoCrearView.as_view(), name='gestion_equipo_crear'),
    path('gestion/equipos/<slug:slug>/editar/', gestion_views.GestionEquipoEditarView.as_view(), name='gestion_equipo_editar'),
    path('gestion/equipos/<slug:slug>/eliminar/', gestion_views.GestionEquipoEliminarView.as_view(), name='gestion_equipo_eliminar'),

    # ─── Gestión: Categorías ─────────────────────────────
    path('gestion/categorias/', gestion_views.GestionCategoriasListView.as_view(), name='gestion_categorias'),
    path('gestion/categorias/nueva/', gestion_views.GestionCategoriaCrearView.as_view(), name='gestion_categoria_crear'),
    path('gestion/categorias/<slug:slug>/editar/', gestion_views.GestionCategoriaEditarView.as_view(), name='gestion_categoria_editar'),
    path('gestion/categorias/<slug:slug>/eliminar/', gestion_views.GestionCategoriaEliminarView.as_view(), name='gestion_categoria_eliminar'),

    # ─── Gestión: Reservas ───────────────────────────────
    path('gestion/reservas/', gestion_views.GestionReservasListView.as_view(), name='gestion_reservas'),
    path('gestion/reservas/<uuid:pk>/', gestion_views.GestionReservaDetailView.as_view(), name='gestion_reserva_detalle'),

    # ─── Gestión: Usuarios ───────────────────────────────
    path('gestion/usuarios/', gestion_views.GestionUsuariosListView.as_view(), name='gestion_usuarios'),
    path('gestion/usuarios/<uuid:pk>/', gestion_views.GestionUsuarioDetailView.as_view(), name='gestion_usuario_detalle'),

    # ─── Gestión: Bloqueos ───────────────────────────────
    path('gestion/bloqueos/', gestion_views.GestionBloqueosListView.as_view(), name='gestion_bloqueos'),
    path('gestion/bloqueos/nuevo/', gestion_views.GestionBloqueoCrearView.as_view(), name='gestion_bloqueo_crear'),
    path('gestion/bloqueos/nuevo/<slug:equipo_slug>/', gestion_views.GestionBloqueoCrearView.as_view(), name='gestion_bloqueo_crear_equipo'),
    path('gestion/bloqueos/<int:pk>/editar/', gestion_views.GestionBloqueoEditarView.as_view(), name='gestion_bloqueo_editar'),
    path('gestion/bloqueos/<int:pk>/eliminar/', gestion_views.GestionBloqueoEliminarView.as_view(), name='gestion_bloqueo_eliminar'),

    # ─── Reportes (DI: PDF / Excel) ──────────────────────
    path('reportes/equipos/', reporte_views.ReporteEquiposView.as_view(), name='reporte_equipos'),

    # ─── Servicio Aliados (consumo de servicio externo) ──
    path('aliados/', views.AliadosView.as_view(), name='aliados'),

    # ─── Gestión: Pagos ──────────────────────────────────
    path('gestion/pagos/', gestion_views.GestionPagosListView.as_view(), name='gestion_pagos'),
]
