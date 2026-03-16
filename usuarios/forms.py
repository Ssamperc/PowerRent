from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.conf import settings
from .models import Usuario

FC = {'class': 'form-control'}
FS = {'class': 'form-select'}


class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario de registro unificado.
    El usuario elige si es Cliente o Administrador.
    Si elige Administrador debe ingresar el código de verificación.
    """
    first_name = forms.CharField(max_length=100, label='Nombre', required=True,
                                 widget=forms.TextInput(attrs=FC))
    last_name = forms.CharField(max_length=100, label='Apellido', required=True,
                                widget=forms.TextInput(attrs=FC))
    email = forms.EmailField(required=True, label='Correo Electrónico',
                             widget=forms.EmailInput(attrs=FC))
    telefono = forms.CharField(max_length=20, required=False, label='Teléfono',
                               widget=forms.TextInput(attrs=FC))
    ciudad = forms.CharField(max_length=100, required=False, label='Ciudad',
                             widget=forms.TextInput(attrs=FC))
    tipo_usuario = forms.ChoiceField(
        label='Tipo de Cuenta',
        choices=Usuario.TipoUsuario.choices,
        initial=Usuario.TipoUsuario.CLIENTE,
        widget=forms.Select(attrs=FS),
    )
    codigo_admin = forms.CharField(
        label='Código de Administrador',
        required=False,
        widget=forms.TextInput(attrs={**FC, 'placeholder': 'Solo para cuentas de administrador'}),
        help_text='Ingresa el código de verificación si registras una cuenta de administrador.',
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'telefono', 'ciudad', 'tipo_usuario', 'codigo_admin',
            'password1', 'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs=FC),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update(FC)
        self.fields['password2'].widget.attrs.update(FC)
        self.fields['username'].help_text = 'Solo letras, dígitos y @/./+/-/_ .'

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_usuario')
        codigo = cleaned_data.get('codigo_admin', '').strip()
        codigo_correcto = getattr(settings, 'ADMIN_REGISTRATION_CODE', 'POWERRENT-ADMIN-2024')

        if tipo == Usuario.TipoUsuario.ADMINISTRADOR:
            if not codigo:
                self.add_error('codigo_admin',
                               'Se requiere el código de verificación para registrar un administrador.')
            elif codigo != codigo_correcto:
                self.add_error('codigo_admin',
                               'Código de administrador incorrecto.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo_usuario = self.cleaned_data['tipo_usuario']
        if user.tipo_usuario == Usuario.TipoUsuario.ADMINISTRADOR:
            user.is_staff = True
        if commit:
            user.save()
        return user


# Alias for backwards compatibility
RegistroClienteForm = RegistroUsuarioForm


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario de edición de perfil"""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'ciudad', 'codigo_postal']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }
        widgets = {
            'first_name': forms.TextInput(attrs=FC),
            'last_name': forms.TextInput(attrs=FC),
            'email': forms.EmailInput(attrs=FC),
            'telefono': forms.TextInput(attrs=FC),
            'direccion': forms.Textarea(attrs={**FC, 'rows': 3}),
            'ciudad': forms.TextInput(attrs=FC),
            'codigo_postal': forms.TextInput(attrs=FC),
        }


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión personalizado"""
    username = forms.CharField(label='Usuario o Email',
                               widget=forms.TextInput(attrs=FC))
    password = forms.CharField(label='Contraseña',
                               widget=forms.PasswordInput(attrs=FC))
