"""
Utilidades compartidas para toda la aplicación PowerRent
"""

import logging
import random
import string
from typing import Optional

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def enviar_email_notificacion(
    destinatario: str,
    asunto: str,
    mensaje: str,
    html_mensaje: Optional[str] = None
) -> bool:
    """
    Envía un email de notificación al usuario.

    Args:
        destinatario: Email del destinatario
        asunto: Asunto del correo
        mensaje: Cuerpo del mensaje en texto plano
        html_mensaje: Cuerpo del mensaje en HTML (opcional)

    Returns:
        bool: True si el email fue enviado exitosamente
    """
    if not destinatario:
        logger.warning("Se intentó enviar email sin destinatario")
        return False

    try:
        remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@powerrent.co')
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=remitente,
            recipient_list=[destinatario],
            html_message=html_mensaje,
            fail_silently=False,
        )
        logger.info(f"Email enviado a {destinatario}: {asunto}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {destinatario}: {e}")
        return False


def formatear_precio(valor) -> str:
    """Formatea un precio decimal para mostrar en la UI"""
    try:
        return f"${valor:,.0f} COP"
    except (TypeError, ValueError):
        return "$0 COP"


def calcular_porcentaje(parte, total) -> float:
    """Calcula el porcentaje de forma segura (evita división por cero)"""
    if not total or total == 0:
        return 0.0
    return round((float(parte) / float(total)) * 100, 1)


def truncar_texto(texto: str, max_largo: int = 100) -> str:
    """Trunca texto a un máximo de caracteres"""
    if len(texto) <= max_largo:
        return texto
    return texto[:max_largo - 3] + "..."


def generar_codigo_unico(prefijo: str, modelo_clase, campo: str = 'codigo_interno') -> str:
    """
    Genera un código único para un modelo dado.

    Args:
        prefijo: Prefijo del código (ej: 'EQ', 'CAT')
        modelo_clase: Clase del modelo Django
        campo: Nombre del campo único

    Returns:
        str: Código único generado
    """
    while True:
        sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        codigo = f"{prefijo}-{sufijo}"
        if not modelo_clase.objects.filter(**{campo: codigo}).exists():
            return codigo
