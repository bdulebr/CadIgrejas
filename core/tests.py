from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models import Membro

@override_settings(AXES_ENABLED=False)
class CoreTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = Membro.objects.create_superuser(
            username='admin_core',
            email='core@teste.com',
            password='password123',
            cpf='00011122233'
        )

    def test_login_sucesso(self):
        response = self.client.post(reverse('login'), {
            'username': 'core@teste.com',
            'password': 'password123'
        })
        # Should redirect to dashboard or perfil if incomplete
        self.assertEqual(response.status_code, 302)
        # Since password is 'password123' and no telefone is provided, the middleware forces them to /perfil/
        self.assertEqual(response.url, '/perfil/')

    def test_login_falha(self):
        response = self.client.post(reverse('login'), {
            'username': 'core@teste.com',
            'password': 'wrongpassword'
        })
        # Should rerender login
        self.assertEqual(response.status_code, 200)

    def test_dashboard_acesso(self):
        self.client.login(username='core@teste.com', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_deslogado(self):
        response = self.client.get(reverse('dashboard'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
