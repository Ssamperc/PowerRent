from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from core.models import Notificacion


class NotificacionesListView(LoginRequiredMixin, ListView):
    model = Notificacion
    template_name = 'notificaciones/lista.html'
    context_object_name = 'notificaciones'
    paginate_by = 20

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_no_leidas'] = Notificacion.objects.filter(
            usuario=self.request.user, leida=False
        ).count()
        return ctx


class MarcarLeidaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notif.marcar_leida()
        redirect_url = notif.url or request.META.get('HTTP_REFERER', '/')
        return redirect(redirect_url)

    def get(self, request, pk):
        return self.post(request, pk)


class MarcarTodasLeidasView(LoginRequiredMixin, View):
    def post(self, request):
        from django.utils import timezone
        Notificacion.objects.filter(usuario=request.user, leida=False).update(
            leida=True, leida_at=timezone.now()
        )
        return redirect('core:notificaciones')
