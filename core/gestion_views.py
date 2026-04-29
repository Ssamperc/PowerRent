"""
Vistas de gestión web (CRUD) para administradores.
Accesibles desde /gestion/ — solo para usuarios con rol administrador.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.utils import timezone
from decimal import Decimal

from core.mixins import AdminRequiredMixin
from equipos.models import Equipo, Categoria, BloqueoDisponibilidad, CalificacionEquipo
from equipos.forms import EquipoForm, CategoriaForm, BloqueoDisponibilidadForm
from reservas.models import Reserva
from pagos.models import Pago
from usuarios.models import Usuario


# ─────────────────────────────────────────────────────────
#  PANEL PRINCIPAL DE GESTIÓN
# ─────────────────────────────────────────────────────────

class GestionInicioView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        return redirect('core:gestion_equipos')


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE EQUIPOS
# ─────────────────────────────────────────────────────────

class GestionEquiposListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Equipo
    template_name = 'gestion/equipos/lista.html'
    context_object_name = 'equipos'
    paginate_by = 20

    def get_queryset(self):
        qs = Equipo.objects.select_related('categoria').order_by('-created_at')
        q = self.request.GET.get('q', '')
        estado = self.request.GET.get('estado', '')
        categoria = self.request.GET.get('categoria', '')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo_interno__icontains=q) | Q(marca__icontains=q))
        if estado:
            qs = qs.filter(estado=estado)
        if categoria:
            qs = qs.filter(categoria__slug=categoria)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categorias'] = Categoria.objects.filter(activo=True)
        ctx['estados'] = Equipo.EstadoEquipo.choices
        ctx['q'] = self.request.GET.get('q', '')
        ctx['estado_sel'] = self.request.GET.get('estado', '')
        ctx['cat_sel'] = self.request.GET.get('categoria', '')
        return ctx


class GestionEquipoCrearView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Equipo
    form_class = EquipoForm
    template_name = 'gestion/equipos/form.html'
    success_url = reverse_lazy('core:gestion_equipos')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Equipo'
        ctx['accion'] = 'Crear'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Equipo "{form.cleaned_data["nombre"]}" creado exitosamente.')
        return super().form_valid(form)


class GestionEquipoEditarView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Equipo
    form_class = EquipoForm
    template_name = 'gestion/equipos/form.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('core:gestion_equipos')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar: {self.object.nombre}'
        ctx['accion'] = 'Guardar Cambios'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Equipo "{self.object.nombre}" actualizado.')
        return super().form_valid(form)


class GestionEquipoEliminarView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Equipo
    template_name = 'gestion/confirmar_eliminar.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('core:gestion_equipos')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Eliminar Equipo'
        ctx['objeto'] = self.object.nombre
        ctx['volver_url'] = reverse_lazy('core:gestion_equipos')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Equipo "{self.object.nombre}" eliminado.')
        return super().form_valid(form)


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE CATEGORÍAS
# ─────────────────────────────────────────────────────────

class GestionCategoriasListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Categoria
    template_name = 'gestion/categorias/lista.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        return Categoria.objects.annotate(
            total=Count('equipos'),
            disponibles=Count('equipos', filter=Q(equipos__disponible=True, equipos__activo=True))
        ).order_by('orden', 'nombre')


class GestionCategoriaCrearView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'gestion/categorias/form.html'
    success_url = reverse_lazy('core:gestion_categorias')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Categoría'
        ctx['accion'] = 'Crear'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.cleaned_data["nombre"]}" creada.')
        return super().form_valid(form)


class GestionCategoriaEditarView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'gestion/categorias/form.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('core:gestion_categorias')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar: {self.object.nombre}'
        ctx['accion'] = 'Guardar Cambios'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{self.object.nombre}" actualizada.')
        return super().form_valid(form)


class GestionCategoriaEliminarView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'gestion/confirmar_eliminar.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('core:gestion_categorias')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Eliminar Categoría'
        ctx['objeto'] = self.object.nombre
        ctx['volver_url'] = reverse_lazy('core:gestion_categorias')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{self.object.nombre}" eliminada.')
        return super().form_valid(form)


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE RESERVAS
# ─────────────────────────────────────────────────────────

class GestionReservasListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Reserva
    template_name = 'gestion/reservas/lista.html'
    context_object_name = 'reservas'
    paginate_by = 25

    def get_queryset(self):
        qs = Reserva.objects.select_related(
            'cliente', 'equipo', 'equipo__categoria'
        ).order_by('-created_at')
        estado = self.request.GET.get('estado', '')
        q = self.request.GET.get('q', '')
        if estado:
            qs = qs.filter(estado=estado)
        if q:
            qs = qs.filter(
                Q(numero_reserva__icontains=q) |
                Q(cliente__username__icontains=q) |
                Q(cliente__first_name__icontains=q) |
                Q(cliente__last_name__icontains=q) |
                Q(equipo__nombre__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = Reserva.EstadoReserva.choices
        ctx['estado_sel'] = self.request.GET.get('estado', '')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['pendientes'] = Reserva.objects.filter(estado=Reserva.EstadoReserva.PENDIENTE).count()
        return ctx


class GestionReservaDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Reserva
    template_name = 'gestion/reservas/detalle.html'
    context_object_name = 'reserva'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pagos'] = self.object.pagos.all()
        return ctx

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        accion = request.POST.get('accion')
        notas = request.POST.get('notas_admin', '').strip()

        if notas:
            reserva.notas_admin = notas
            reserva.save(update_fields=['notas_admin'])

        from core.notificaciones import NotificacionService

        try:
            if accion == 'confirmar':
                reserva.confirmar_reserva()
                NotificacionService.reserva_confirmada(reserva)
                messages.success(request, f'Reserva {reserva.numero_reserva} confirmada.')
            elif accion == 'iniciar':
                reserva.iniciar_alquiler()
                NotificacionService.reserva_en_curso(reserva)
                messages.success(request, f'Alquiler de {reserva.equipo.nombre} iniciado.')
            elif accion == 'completar':
                reserva.completar_alquiler()
                NotificacionService.reserva_completada(reserva)
                messages.success(request, f'Alquiler de {reserva.equipo.nombre} completado.')
            elif accion == 'cancelar':
                reserva.cancelar_reserva()
                NotificacionService.reserva_cancelada(reserva)
                messages.warning(request, f'Reserva {reserva.numero_reserva} cancelada.')
            elif notas:
                messages.success(request, 'Notas actualizadas.')
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('core:gestion_reserva_detalle', pk=reserva.pk)


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE USUARIOS
# ─────────────────────────────────────────────────────────

class GestionUsuariosListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Usuario
    template_name = 'gestion/usuarios/lista.html'
    context_object_name = 'usuarios'
    paginate_by = 25

    def get_queryset(self):
        qs = Usuario.objects.annotate(
            total_reservas=Count('reservas')
        ).order_by('-created_at')
        tipo = self.request.GET.get('tipo', '')
        q = self.request.GET.get('q', '')
        if tipo:
            qs = qs.filter(tipo_usuario=tipo)
        if q:
            qs = qs.filter(
                Q(username__icontains=q) | Q(first_name__icontains=q) |
                Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos'] = Usuario.TipoUsuario.choices
        ctx['tipo_sel'] = self.request.GET.get('tipo', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class GestionUsuarioDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Usuario
    template_name = 'gestion/usuarios/detalle.html'
    context_object_name = 'usuario_obj'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reservas'] = self.object.reservas.select_related('equipo').order_by('-created_at')[:10]
        ctx['pagos'] = self.object.pagos.order_by('-fecha_pago')[:10]
        return ctx

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()
        accion = request.POST.get('accion')

        if usuario == request.user:
            messages.error(request, 'No puedes modificar tu propio rol.')
            return redirect('core:gestion_usuario_detalle', pk=usuario.pk)

        if accion == 'toggle_rol':
            if usuario.es_administrador:
                usuario.tipo_usuario = Usuario.TipoUsuario.CLIENTE
                messages.success(request, f'{usuario.username} cambió a Cliente.')
            else:
                usuario.tipo_usuario = Usuario.TipoUsuario.ADMINISTRADOR
                messages.success(request, f'{usuario.username} cambió a Administrador.')
            usuario.save(update_fields=['tipo_usuario'])
        elif accion == 'toggle_activo':
            usuario.is_active = not usuario.is_active
            estado = 'activado' if usuario.is_active else 'desactivado'
            usuario.save(update_fields=['is_active'])
            messages.success(request, f'Usuario {usuario.username} {estado}.')

        return redirect('core:gestion_usuario_detalle', pk=usuario.pk)


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE BLOQUEOS DE DISPONIBILIDAD
# ─────────────────────────────────────────────────────────

class GestionBloqueosListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = BloqueoDisponibilidad
    template_name = 'gestion/bloqueos/lista.html'
    context_object_name = 'bloqueos'
    paginate_by = 25

    def get_queryset(self):
        return BloqueoDisponibilidad.objects.select_related(
            'equipo', 'creado_por'
        ).order_by('-fecha_inicio')


class GestionBloqueoCrearView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = BloqueoDisponibilidad
    form_class = BloqueoDisponibilidadForm
    template_name = 'gestion/bloqueos/form.html'
    success_url = reverse_lazy('core:gestion_bloqueos')

    def get_initial(self):
        initial = super().get_initial()
        equipo_slug = self.kwargs.get('equipo_slug')
        if equipo_slug:
            equipo = get_object_or_404(Equipo, slug=equipo_slug)
            initial['equipo'] = equipo
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Bloqueo de Disponibilidad'
        ctx['accion'] = 'Crear'
        return ctx

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Bloqueo de disponibilidad creado.')
        return super().form_valid(form)


class GestionBloqueoEditarView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = BloqueoDisponibilidad
    form_class = BloqueoDisponibilidadForm
    template_name = 'gestion/bloqueos/form.html'
    success_url = reverse_lazy('core:gestion_bloqueos')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar Bloqueo: {self.object.equipo.nombre}'
        ctx['accion'] = 'Guardar Cambios'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Bloqueo actualizado.')
        return super().form_valid(form)


class GestionBloqueoEliminarView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = BloqueoDisponibilidad
    template_name = 'gestion/confirmar_eliminar.html'
    success_url = reverse_lazy('core:gestion_bloqueos')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Eliminar Bloqueo'
        ctx['objeto'] = str(self.object)
        ctx['volver_url'] = reverse_lazy('core:gestion_bloqueos')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Bloqueo eliminado.')
        return super().form_valid(form)


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE PAGOS (solo lectura)
# ─────────────────────────────────────────────────────────

class GestionPagosListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Pago
    template_name = 'gestion/pagos/lista.html'
    context_object_name = 'pagos'
    paginate_by = 25

    def get_queryset(self):
        qs = Pago.objects.select_related(
            'usuario', 'reserva', 'reserva__equipo'
        ).order_by('-fecha_pago')
        estado = self.request.GET.get('estado', '')
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = Pago.EstadoPago.choices
        ctx['estado_sel'] = self.request.GET.get('estado', '')
        ctx['total_ingresos'] = Pago.objects.filter(
            estado=Pago.EstadoPago.COMPLETADO,
            tipo_pago=Pago.TipoPago.ALQUILER
        ).aggregate(t=Sum('monto'))['t'] or Decimal('0')
        return ctx
