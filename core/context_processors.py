def notificaciones(request):
    """Conteo de notificaciones no leídas."""
    if request.user.is_authenticated:
        from core.models import Notificacion
        count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        return {'notificaciones_no_leidas': count}
    return {'notificaciones_no_leidas': 0}


_tasas_cache = {'data': None, 'ts': 0}

def tasas_cambio(request):
    """Tipo de cambio COP-USD/EUR con caché de 1 hora."""
    import time
    global _tasas_cache
    now = time.time()
    if _tasas_cache['data'] is None or (now - _tasas_cache['ts']) > 3600:
        from .servicios_externos import obtener_tasas_cambio
        _tasas_cache['data'] = obtener_tasas_cambio()
        _tasas_cache['ts'] = now
    return {'tasas_cambio': _tasas_cache['data']}
