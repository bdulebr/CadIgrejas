from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from gestao_membros.models import Departamento, Habilidade

Membro = get_user_model()

class PerfilTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Membro.objects.create_user(
            username="testuser",
            password="password123",
            email="test@pvenseada.org",
            first_name="Test",
            last_name="User"
        )
        self.depto = Departamento.objects.create(nome="Música", categoria="ministerio")
        self.hab1 = Habilidade.objects.create(nome="Baterista", departamento=self.depto)
        self.hab2 = Habilidade.objects.create(nome="Tecladista", departamento=self.depto)
        self.hab_global = Habilidade.objects.create(nome="Aconselhador", departamento=None)

    def test_editar_perfil_carrega_com_sucesso(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('editar_perfil'))
        self.assertEqual(response.status_code, 200)
        # All skills should be loaded in the context regardless of user's department
        self.assertIn(self.hab1, response.context['todas_habilidades'])
        self.assertIn(self.hab_global, response.context['todas_habilidades'])

    def test_editar_perfil_atualiza_dados_e_habilidades(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('editar_perfil'), {
            'first_name': 'Test Updated',
            'last_name': 'User',
            'email': 'test@pvenseada.org',
            'cep': '01001-000',
            'endereco': 'Praça da Sé',
            'bairro': 'Sé',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'habilidades': [self.hab1.id, self.hab_global.id]
        })
        # Should redirect after successful save
        self.assertRedirects(response, reverse('editar_perfil'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test Updated')
        self.assertEqual(self.user.cep, '01001-000')
        self.assertEqual(self.user.estado, 'SP')

        # Verify skills were saved
        user_habs = self.user.habilidades.all()
        self.assertEqual(user_habs.count(), 2)
        self.assertIn(self.hab1, user_habs)
        self.assertIn(self.hab_global, user_habs)
        self.assertNotIn(self.hab2, user_habs)
