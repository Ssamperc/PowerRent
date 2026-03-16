from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Usuario
from .forms import RegistroUsuarioForm, PerfilUsuarioForm, LoginForm


class RegistroView(CreateView):
    model = Usuario
    form_class = RegistroUsuarioForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('usuarios:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        tipo = self.object.get_tipo_usuario_display()
        messages.success(
            self.request,
            f'¡Cuenta de {tipo} creada exitosamente! Ahora puedes iniciar sesión.'
        )
        try:
            from core.notificaciones import NotificacionService
            NotificacionService.nuevo_usuario(self.object)
        except Exception:
            pass
        return response


class LoginPersonalizadoView(LoginView):
    form_class = LoginForm
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.es_administrador:
            return reverse_lazy('core:gestion_equipos')
        return reverse_lazy('equipos:lista')


class PerfilView(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'usuarios/perfil.html'
    context_object_name = 'usuario'

    def get_object(self):
        return self.request.user


class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = PerfilUsuarioForm
    template_name = 'usuarios/editar_perfil.html'
    success_url = reverse_lazy('usuarios:perfil')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)
