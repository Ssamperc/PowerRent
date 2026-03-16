from django import forms
from django.utils.text import slugify
from .models import Equipo, Categoria, BloqueoDisponibilidad, CalificacionEquipo

FC = {'class': 'form-control'}
FC_SM = {'class': 'form-control form-control-sm'}
FC_SELECT = {'class': 'form-select'}
FC_CHECK = {'class': 'form-check-input'}


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs=FC),
            'descripcion': forms.Textarea(attrs={**FC, 'rows': 3}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs=FC),
            'activo': forms.CheckboxInput(attrs=FC_CHECK),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.nombre)
        if commit:
            obj.save()
        return obj


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = [
            'nombre', 'descripcion', 'categoria',
            'codigo_interno', 'marca', 'modelo', 'numero_serie',
            'precio_por_dia', 'precio_por_semana', 'precio_por_mes', 'deposito_garantia',
            'estado', 'disponible', 'activo',
            'imagen_principal',
            'ultima_fecha_mantenimiento', 'proxima_fecha_mantenimiento',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs=FC),
            'descripcion': forms.Textarea(attrs={**FC, 'rows': 3}),
            'categoria': forms.Select(attrs=FC_SELECT),
            'codigo_interno': forms.TextInput(attrs=FC),
            'marca': forms.TextInput(attrs=FC),
            'modelo': forms.TextInput(attrs=FC),
            'numero_serie': forms.TextInput(attrs=FC),
            'precio_por_dia': forms.NumberInput(attrs={**FC, 'step': '0.01'}),
            'precio_por_semana': forms.NumberInput(attrs={**FC, 'step': '0.01'}),
            'precio_por_mes': forms.NumberInput(attrs={**FC, 'step': '0.01'}),
            'deposito_garantia': forms.NumberInput(attrs={**FC, 'step': '0.01'}),
            'estado': forms.Select(attrs=FC_SELECT),
            'disponible': forms.CheckboxInput(attrs=FC_CHECK),
            'activo': forms.CheckboxInput(attrs=FC_CHECK),
            'imagen_principal': forms.FileInput(attrs={'class': 'form-control'}),
            'ultima_fecha_mantenimiento': forms.DateInput(attrs={**FC, 'type': 'date'}),
            'proxima_fecha_mantenimiento': forms.DateInput(attrs={**FC, 'type': 'date'}),
        }


class BloqueoDisponibilidadForm(forms.ModelForm):
    class Meta:
        model = BloqueoDisponibilidad
        fields = ['equipo', 'fecha_inicio', 'fecha_fin', 'tipo_motivo', 'motivo', 'activo']
        widgets = {
            'equipo': forms.Select(attrs=FC_SELECT),
            'fecha_inicio': forms.DateInput(attrs={**FC, 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={**FC, 'type': 'date'}),
            'tipo_motivo': forms.Select(attrs=FC_SELECT),
            'motivo': forms.Textarea(attrs={**FC, 'rows': 2}),
            'activo': forms.CheckboxInput(attrs=FC_CHECK),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        return cleaned_data


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = CalificacionEquipo
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.RadioSelect(choices=[(i, f'{i} estrella{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={**FC, 'rows': 4,
                                                'placeholder': 'Comparte tu experiencia con este equipo...'}),
        }
        labels = {
            'puntuacion': 'Puntuación',
            'comentario': 'Comentario (opcional)',
        }


class ReservaAdminForm(forms.Form):
    """Formulario para agregar notas de admin a una reserva."""
    notas_admin = forms.CharField(
        label='Notas internas',
        required=False,
        widget=forms.Textarea(attrs={**FC, 'rows': 3,
                                     'placeholder': 'Notas visibles solo para administradores...'}),
    )
