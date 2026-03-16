from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_active', 'created_at']
    list_filter = ['tipo_usuario', 'is_active', 'email_verificado']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telefono']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Información PowerRent', {
            'fields': ('tipo_usuario', 'telefono', 'direccion', 'ciudad', 'codigo_postal',
                       'email_verificado', 'telefono_verificado')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información PowerRent', {
            'fields': ('tipo_usuario', 'email', 'first_name', 'last_name', 'telefono', 'ciudad')
        }),
    )
