from django.test import TestCase
from django.urls import reverse
from .models import Usuario


class UsuarioModelTest(TestCase):

    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente1',
            email='cliente@test.com',
            password='testpass123',
            tipo_usuario=Usuario.TipoUsuario.CLIENTE
        )
        self.admin = Usuario.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123',
            tipo_usuario=Usuario.TipoUsuario.ADMINISTRADOR
        )

    def test_usuario_es_cliente(self):
        self.assertTrue(self.cliente.es_cliente)
        self.assertFalse(self.cliente.es_administrador)

    def test_usuario_es_administrador(self):
        self.assertTrue(self.admin.es_administrador)
        self.assertFalse(self.admin.es_cliente)

    def test_cliente_puede_realizar_reservas(self):
        self.assertTrue(self.cliente.puede_realizar_reservas())

    def test_cliente_no_puede_gestionar_equipos(self):
        self.assertFalse(self.cliente.puede_gestionar_equipos())

    def test_admin_puede_gestionar_equipos(self):
        self.assertTrue(self.admin.puede_gestionar_equipos())

    def test_str_usuario(self):
        self.assertIn('Cliente', str(self.cliente))
