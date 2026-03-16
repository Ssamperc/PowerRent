"""
Servicio de notificaciones — crea notificaciones internas para usuarios.
Llamar desde services.py de cada app al ocurrir eventos de negocio.
"""
from core.models import Notificacion


class NotificacionService:

    @staticmethod
    def crear(usuario, tipo, titulo, mensaje, url=''):
        """Crea una notificación para un usuario."""
        Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            url=url,
        )

    @staticmethod
    def notificar_admins(tipo, titulo, mensaje, url=''):
        """Envía una notificación a todos los administradores activos."""
        from usuarios.models import Usuario
        admins = Usuario.objects.filter(
            tipo_usuario=Usuario.TipoUsuario.ADMINISTRADOR,
            is_active=True
        )
        for admin in admins:
            NotificacionService.crear(admin, tipo, titulo, mensaje, url)

    # ─── Reservas ────────────────────────────────────────────────

    @staticmethod
    def reserva_creada(reserva):
        url = f'/reservas/{reserva.pk}/'
        NotificacionService.crear(
            reserva.cliente,
            Notificacion.Tipo.RESERVA_CREADA,
            f'Reserva {reserva.numero_reserva} creada',
            f'Tu reserva de "{reserva.equipo.nombre}" del {reserva.fecha_inicio} al {reserva.fecha_fin} fue recibida. '
            f'Costo: ${reserva.costo_alquiler:,.0f}. Pendiente de confirmación.',
            url,
        )
        NotificacionService.notificar_admins(
            Notificacion.Tipo.ADMIN_NUEVA_RESERVA,
            f'Nueva reserva de {reserva.cliente.get_full_name() or reserva.cliente.username}',
            f'{reserva.cliente.get_full_name() or reserva.cliente.username} solicitó "{reserva.equipo.nombre}" '
            f'del {reserva.fecha_inicio} al {reserva.fecha_fin}. Monto: ${reserva.costo_alquiler:,.0f}.',
            url,
        )

    @staticmethod
    def reserva_confirmada(reserva):
        url = f'/reservas/{reserva.pk}/'
        NotificacionService.crear(
            reserva.cliente,
            Notificacion.Tipo.RESERVA_CONFIRMADA,
            f'¡Reserva {reserva.numero_reserva} confirmada!',
            f'Tu reserva de "{reserva.equipo.nombre}" del {reserva.fecha_inicio} al {reserva.fecha_fin} '
            f'ha sido confirmada. ¡Todo listo!',
            url,
        )

    @staticmethod
    def reserva_cancelada(reserva):
        url = f'/reservas/{reserva.pk}/'
        NotificacionService.crear(
            reserva.cliente,
            Notificacion.Tipo.RESERVA_CANCELADA,
            f'Reserva {reserva.numero_reserva} cancelada',
            f'Tu reserva de "{reserva.equipo.nombre}" del {reserva.fecha_inicio} al {reserva.fecha_fin} '
            f'ha sido cancelada.',
            url,
        )

    @staticmethod
    def reserva_en_curso(reserva):
        url = f'/reservas/{reserva.pk}/'
        NotificacionService.crear(
            reserva.cliente,
            Notificacion.Tipo.RESERVA_EN_CURSO,
            f'Alquiler de {reserva.equipo.nombre} iniciado',
            f'El alquiler de "{reserva.equipo.nombre}" ha comenzado. '
            f'Fecha de devolución: {reserva.fecha_fin}.',
            url,
        )

    @staticmethod
    def reserva_completada(reserva):
        url = f'/reservas/{reserva.pk}/'
        NotificacionService.crear(
            reserva.cliente,
            Notificacion.Tipo.RESERVA_COMPLETADA,
            f'Alquiler completado — ¡califica tu experiencia!',
            f'El alquiler de "{reserva.equipo.nombre}" ha finalizado. '
            f'¡Cuéntanos cómo fue tu experiencia calificando el equipo!',
            f'/equipos/{reserva.equipo.slug}/calificar/',
        )

    # ─── Pagos ───────────────────────────────────────────────────

    @staticmethod
    def pago_recibido(pago):
        url = f'/pagos/{pago.pk}/'
        NotificacionService.crear(
            pago.usuario,
            Notificacion.Tipo.PAGO_RECIBIDO,
            f'Pago {pago.numero_transaccion} recibido',
            f'Recibimos tu pago de ${pago.monto:,.0f} por la reserva {pago.reserva.numero_reserva}.',
            url,
        )

    # ─── Usuarios ────────────────────────────────────────────────

    @staticmethod
    def nuevo_usuario(usuario):
        NotificacionService.notificar_admins(
            Notificacion.Tipo.ADMIN_NUEVO_USUARIO,
            f'Nuevo usuario: {usuario.get_full_name() or usuario.username}',
            f'Se registró {usuario.get_full_name() or usuario.username} ({usuario.email}) '
            f'como {usuario.get_tipo_usuario_display()}.',
            f'/gestion/usuarios/',
        )

    # ─── Calificaciones ──────────────────────────────────────────

    @staticmethod
    def nueva_calificacion(calificacion):
        NotificacionService.notificar_admins(
            Notificacion.Tipo.NUEVA_CALIFICACION,
            f'Nueva calificación: {calificacion.equipo.nombre}',
            f'{calificacion.cliente.get_full_name() or calificacion.cliente.username} calificó '
            f'"{calificacion.equipo.nombre}" con {calificacion.puntuacion}⭐.',
            f'/equipos/{calificacion.equipo.slug}/',
        )
