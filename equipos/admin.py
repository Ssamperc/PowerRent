from django.contrib import admin
from .models import Categoria, Equipo, ImagenEquipo, BloqueoDisponibilidad, CalificacionEquipo


class ImagenEquipoInline(admin.TabularInline):
    model = ImagenEquipo
    extra = 1
    fields = ['imagen', 'descripcion', 'orden']


class BloqueoDisponibilidadInline(admin.TabularInline):
    model = BloqueoDisponibilidad
    extra = 0
    fields = ['fecha_inicio', 'fecha_fin', 'tipo_motivo', 'motivo', 'activo']
    readonly_fields = []


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'total_equipos', 'equipos_disponibles', 'orden', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ['orden', 'nombre']


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'codigo_interno', 'categoria', 'precio_por_dia',
        'estado', 'disponible', 'activo', 'requiere_mantenimiento'
    ]
    list_filter = ['categoria', 'estado', 'disponible', 'activo']
    search_fields = ['nombre', 'codigo_interno', 'marca', 'modelo', 'numero_serie']
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ImagenEquipoInline, BloqueoDisponibilidadInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion', 'categoria', 'imagen_principal')
        }),
        ('Identificación', {
            'fields': ('codigo_interno', 'marca', 'modelo', 'numero_serie')
        }),
        ('Precios (DecimalField - nunca float)', {
            'fields': ('precio_por_dia', 'precio_por_semana', 'precio_por_mes', 'deposito_garantia'),
            'description': 'Todos los precios usan DecimalField para precisión exacta en operaciones monetarias'
        }),
        ('Estado', {
            'fields': ('estado', 'disponible', 'activo')
        }),
        ('Mantenimiento', {
            'fields': ('ultima_fecha_mantenimiento', 'proxima_fecha_mantenimiento'),
            'classes': ('collapse',)
        }),
        ('Especificaciones Técnicas', {
            'fields': ('especificaciones',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['marcar_disponible', 'marcar_mantenimiento', 'marcar_fuera_servicio']

    def requiere_mantenimiento(self, obj):
        return obj.requiere_mantenimiento()
    requiere_mantenimiento.boolean = True
    requiere_mantenimiento.short_description = '¿Necesita mantenimiento?'

    def marcar_disponible(self, request, queryset):
        for equipo in queryset:
            equipo.marcar_como_disponible()
        self.message_user(request, f'{queryset.count()} equipos marcados como disponibles.')
    marcar_disponible.short_description = 'Marcar como disponible'

    def marcar_mantenimiento(self, request, queryset):
        queryset.update(estado=Equipo.EstadoEquipo.MANTENIMIENTO, disponible=False)
        self.message_user(request, f'{queryset.count()} equipos enviados a mantenimiento.')
    marcar_mantenimiento.short_description = 'Enviar a mantenimiento'

    def marcar_fuera_servicio(self, request, queryset):
        queryset.update(estado=Equipo.EstadoEquipo.FUERA_SERVICIO, disponible=False)
        self.message_user(request, f'{queryset.count()} equipos marcados como fuera de servicio.')
    marcar_fuera_servicio.short_description = 'Marcar fuera de servicio'


@admin.register(ImagenEquipo)
class ImagenEquipoAdmin(admin.ModelAdmin):
    list_display = ['equipo', 'descripcion', 'orden', 'created_at']
    list_filter = ['equipo__categoria']
    search_fields = ['equipo__nombre', 'descripcion']


@admin.register(BloqueoDisponibilidad)
class BloqueoDisponibilidadAdmin(admin.ModelAdmin):
    list_display = [
        'equipo', 'fecha_inicio', 'fecha_fin',
        'tipo_motivo', 'motivo', 'activo', 'creado_por'
    ]
    list_filter = ['tipo_motivo', 'activo', 'equipo__categoria']
    search_fields = ['equipo__nombre', 'motivo']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['equipo']


@admin.register(CalificacionEquipo)
class CalificacionEquipoAdmin(admin.ModelAdmin):
    list_display = ['equipo', 'cliente', 'puntuacion', 'created_at']
    list_filter = ['puntuacion']
    search_fields = ['equipo__nombre', 'cliente__username', 'comentario']
    readonly_fields = ['created_at']
