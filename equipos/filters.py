import django_filters
from .models import Equipo, Categoria


class EquipoFilter(django_filters.FilterSet):
    """Filtros para la búsqueda de equipos"""
    nombre = django_filters.CharFilter(lookup_expr='icontains', label='Nombre')
    categoria = django_filters.ModelChoiceFilter(queryset=Categoria.objects.filter(activo=True), label='Categoría')
    precio_min = django_filters.NumberFilter(field_name='precio_por_dia', lookup_expr='gte', label='Precio mínimo/día')
    precio_max = django_filters.NumberFilter(field_name='precio_por_dia', lookup_expr='lte', label='Precio máximo/día')
    marca = django_filters.CharFilter(lookup_expr='icontains', label='Marca')

    class Meta:
        model = Equipo
        fields = ['nombre', 'categoria', 'marca', 'precio_min', 'precio_max']
