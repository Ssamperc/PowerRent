from django.contrib import admin
from django.utils import timezone
from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_reserva', 'cliente', 'equipo', 'fecha_inicio', 'fecha_fin',
        'estado', 'costo_alquiler', 'created_at'
    ]
    list_filter = ['estado', 'fecha_inicio', 'fecha_fin']
    search_fields = ['numero_reserva', 'cliente__username', 'cliente__email', 'equipo__nombre']
    readonly_fields = ['numero_reserva', 'created_at', 'updated_at', 'confirmada_at', 'costo_alquiler']
    ordering = ['-created_at']

    fieldsets = (
        ('Información General', {
            'fields': ('numero_reserva', 'cliente', 'equipo', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin', 'fecha_entrega_real', 'fecha_devolucion_real', 'confirmada_at')
        }),
        ('Costos', {
            'fields': ('costo_alquiler', 'deposito_pagado', 'costo_adicional')
        }),
        ('Notas', {
            'fields': ('notas_cliente', 'notas_admin')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirmar_reservas', 'cancelar_reservas', 'iniciar_alquiler', 'completar_alquiler']

    def confirmar_reservas(self, request, queryset):
        count = 0
        for reserva in queryset.filter(estado=Reserva.EstadoReserva.PENDIENTE):
            try:
                reserva.confirmar_reserva()
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {reserva.numero_reserva}: {e}", level='error')
        self.message_user(request, f'{count} reservas confirmadas.')
    confirmar_reservas.short_description = 'Confirmar reservas seleccionadas'

    def cancelar_reservas(self, request, queryset):
        count = 0
        for reserva in queryset:
            try:
                reserva.cancelar_reserva()
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {reserva.numero_reserva}: {e}", level='error')
        self.message_user(request, f'{count} reservas canceladas.')
    cancelar_reservas.short_description = 'Cancelar reservas seleccionadas'

    def iniciar_alquiler(self, request, queryset):
        count = 0
        for reserva in queryset.filter(estado=Reserva.EstadoReserva.CONFIRMADA):
            try:
                reserva.iniciar_alquiler()
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {reserva.numero_reserva}: {e}", level='error')
        self.message_user(request, f'{count} alquileres iniciados.')
    iniciar_alquiler.short_description = 'Iniciar alquiler (entrega)'

    def completar_alquiler(self, request, queryset):
        count = 0
        for reserva in queryset.filter(estado=Reserva.EstadoReserva.EN_CURSO):
            try:
                reserva.completar_alquiler()
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {reserva.numero_reserva}: {e}", level='error')
        self.message_user(request, f'{count} alquileres completados.')
    completar_alquiler.short_description = 'Completar alquiler (devolución)'
