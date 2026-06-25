from django.test import TestCase, Client
from django.urls import reverse
from core.models import Membro
from ministerio_casais.models import Casal

class CasalMapIntegrationTest(TestCase):
    def setUp(self):
        # Configurar ambiente com um Membro logado
        self.client = Client()
        self.user = Membro.objects.create_user(
            username='test_user',
            password='password123',
            email='test@pvenseada.org',
            cpf='11111111111',
            nivel_hierarquico='super_admin'
        )
        self.client.force_login(self.user)

        # Criar um Casal
        self.casal = Casal.objects.create(
            nome_conjuge_1="João",
            nome_conjuge_2="Maria",
            status_relacionamento="Casados",
            endereco="Rua Teste de Mapa, 123"
        )

    def test_editar_casal_salva_endereco(self):
        url = reverse('editar_casal', args=[self.casal.id])
        data = {
            'nome_conjuge_1': 'João Atualizado',
            'nome_conjuge_2': 'Maria',
            'status_relacionamento': 'Casados',
            'endereco': 'Nova Rua do Mapa, 456'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redireciona em caso de sucesso

        self.casal.refresh_from_db()
        self.assertEqual(self.casal.nome_conjuge_1, 'João Atualizado')
        self.assertEqual(self.casal.endereco, 'Nova Rua do Mapa, 456')

    def test_perfil_casal_renderiza_sem_erros(self):
        url = reverse('perfil_casal', args=[self.casal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste de Mapa, 123')
        self.assertContains(response, 'mapa_osm')  # AlpineJS x-data map integration test
