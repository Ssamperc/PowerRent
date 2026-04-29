"""
Servicios web JSON para PowerRent.
Provee información de equipos disponibles en formato JSON.
"""
import json
import urllib.request
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from equipos.models import Equipo, Categoria


class EquiposDisponiblesAPIView(View):
    """
    API pública: Lista de equipos disponibles para alquiler.
    GET /api/equipos/?categoria=<slug>&precio_max=<precio>
    """

    def get(self, request):
        equipos = Equipo.objects.filter(
            activo=True,
            disponible=True,
        ).select_related('categoria').order_by('-created_at')

        # Filtros opcionales
        categoria = request.GET.get('categoria')
        precio_max = request.GET.get('precio_max')

        if categoria:
            equipos = equipos.filter(categoria__slug=categoria)
        if precio_max:
            try:
                equipos = equipos.filter(precio_por_dia__lte=float(precio_max))
            except ValueError:
                pass

        data = {
            'empresa': 'PowerRent',
            'descripcion': 'Alquiler de equipos de construcción profesional en Colombia',
            'total': equipos.count(),
            'equipos': [
                {
                    'id': str(e.id),
                    'nombre': e.nombre,
                    'slug': e.slug,
                    'categoria': e.categoria.nombre,
                    'categoria_slug': e.categoria.slug,
                    'precio_por_dia': float(e.precio_por_dia),
                    'precio_por_semana': float(e.precio_por_semana) if e.precio_por_semana else None,
                    'precio_por_mes': float(e.precio_por_mes) if e.precio_por_mes else None,
                    'deposito_garantia': float(e.deposito_garantia),
                    'descripcion': e.descripcion[:200],
                    'marca': e.marca,
                    'modelo': e.modelo,
                    'estado': e.estado,
                    'disponible': e.disponible,
                    'url_detalle': request.build_absolute_uri(f'/equipos/{e.slug}/'),
                    'imagen': request.build_absolute_uri(e.imagen_principal.url) if e.imagen_principal else None,
                }
                for e in equipos[:50]
            ]
        }
        response = JsonResponse(data)
        response['Access-Control-Allow-Origin'] = '*'
        return response


class EquipoDetalleAPIView(View):
    """API: Detalle de un equipo específico"""

    def get(self, request, slug):
        try:
            equipo = Equipo.objects.get(slug=slug, activo=True)
        except Equipo.DoesNotExist:
            return JsonResponse({'error': 'Equipo no encontrado'}, status=404)

        data = {
            'id': str(equipo.id),
            'nombre': equipo.nombre,
            'slug': equipo.slug,
            'descripcion': equipo.descripcion,
            'categoria': equipo.categoria.nombre,
            'codigo_interno': equipo.codigo_interno,
            'marca': equipo.marca,
            'modelo': equipo.modelo,
            'numero_serie': equipo.numero_serie,
            'precio_por_dia': float(equipo.precio_por_dia),
            'precio_por_semana': float(equipo.precio_por_semana) if equipo.precio_por_semana else None,
            'precio_por_mes': float(equipo.precio_por_mes) if equipo.precio_por_mes else None,
            'deposito_garantia': float(equipo.deposito_garantia),
            'disponible': equipo.disponible,
            'estado': equipo.estado,
            'especificaciones': equipo.especificaciones_tecnicas or {},
            'url_detalle': request.build_absolute_uri(f'/equipos/{equipo.slug}/'),
        }
        response = JsonResponse(data)
        response['Access-Control-Allow-Origin'] = '*'
        return response


class ServicioAliadosAPIView(View):
    """
    Consume el servicio JSON del equipo aliado (equipo anterior).
    Muestra sus productos/servicios en PowerRent.
    """

    ALIADO_API_URL = 'https://jsonplaceholder.typicode.com/posts?_limit=5'

    def get(self, request):
        try:
            req = urllib.request.Request(
                self.ALIADO_API_URL,
                headers={'User-Agent': 'PowerRent/1.0'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = json.loads(resp.read().decode())
                # Adaptar al formato genérico
                items = [
                    {
                        'id': item.get('id'),
                        'titulo': item.get('title', '')[:80],
                        'descripcion': item.get('body', '')[:200],
                        'fuente': 'Equipo Aliado',
                    }
                    for item in raw
                ]
        except Exception as exc:
            items = []
            return JsonResponse({'error': str(exc), 'items': items}, status=200)

        return JsonResponse({'total': len(items), 'items': items})
