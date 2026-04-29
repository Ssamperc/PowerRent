from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea administrador"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_administrador

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta página.')
        return redirect('core:home')


class ClienteRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea cliente"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_cliente

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta página.')
        return redirect('core:home')
