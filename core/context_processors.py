def notificaciones(request):
    """Agrega el conteo de notificaciones no leídas al contexto global."""
    if request.user.is_authenticated:
        from core.models import Notificacion
        count = Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).count()
        return {'notificaciones_no_leidas': count}
    return {'notificaciones_no_leidas': 0}
