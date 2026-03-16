from django import forms
from django.utils import timezone
from .models import Reserva


class ReservaForm(forms.ModelForm):
    """Formulario para crear una reserva"""

    class Meta:
        model = Reserva
        fields = ['fecha_inicio', 'fecha_fin', 'notas_cliente']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notas_cliente': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'notas_cliente': 'Notas adicionales',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio < timezone.now().date():
                raise forms.ValidationError('La fecha de inicio no puede ser en el pasado.')

            if fecha_fin <= fecha_inicio:
                raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

        return cleaned_data
