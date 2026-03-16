from django.contrib import admin
from django.utils import timezone
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_transaccion', 'reserva', 'usuario', 'monto',
        'tipo_pago', 'metodo_pago', 'estado', 'fecha_pago'
    ]
    list_filter = ['estado', 'tipo_pago', 'metodo_pago', 'fecha_pago']
    search_fields = [
        'numero_transaccion', 'reserva__numero_reserva',
        'usuario__username', 'usuario__email', 'referencia_externa'
    ]
    readonly_fields = ['numero_transaccion', 'created_at', 'updated_at', 'fecha_pago', 'fecha_procesado']
    ordering = ['-fecha_pago']

    fieldsets = (
        ('Información del Pago', {
            'fields': ('numero_transaccion', 'reserva', 'usuario', 'monto', 'tipo_pago', 'metodo_pago', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_pago', 'fecha_procesado'),
        }),
        ('Referencia Externa (Stripe/PayPal)', {
            'fields': ('referencia_externa',),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['marcar_completado', 'procesar_reembolso']

    def marcar_completado(self, request, queryset):
        count = 0
        for pago in queryset.filter(estado__in=[Pago.EstadoPago.PENDIENTE, Pago.EstadoPago.PROCESANDO]):
            try:
                if pago.procesar_pago():
                    count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {pago.numero_transaccion}: {e}", level='error')
        self.message_user(request, f'{count} pagos procesados como completados.')
    marcar_completado.short_description = 'Procesar y completar pagos'

    def procesar_reembolso(self, request, queryset):
        count = 0
        for pago in queryset.filter(estado=Pago.EstadoPago.COMPLETADO):
            try:
                pago.reembolsar(motivo='Reembolso manual desde admin')
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error en {pago.numero_transaccion}: {e}", level='error')
        self.message_user(request, f'{count} pagos reembolsados.')
    procesar_reembolso.short_description = 'Reembolsar pagos seleccionados'
