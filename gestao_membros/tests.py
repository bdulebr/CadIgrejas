from django.test import TestCase, Client
from django.urls import reverse
from core.models import Membro
from gestao_membros.models import Departamento, Funcao

class FuncaoMembroTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Membro.objects.create_user(username='admin', password='123', email='admin@teste.com', nivel_hierarquico='super_admin')
        self.client.force_login(self.user)

        self.dep = Departamento.objects.create(nome='Dep Teste', categoria='departamento')
        self.funcao = Funcao.objects.create(nome='Funcao Teste', departamento=self.dep)
        self.membro = Membro.objects.create_user(username='user1', password='123', email='user1@teste.com')

    def test_vincular_membro(self):
        url = reverse('vincular_membro_funcao', args=[self.funcao.id])
        response = self.client.post(url, {'membro_id': self.membro.id})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.funcao.membros.filter(id=self.membro.id).exists())

    def test_desvincular_membro(self):
        self.funcao.membros.add(self.membro)
        url = reverse('desvincular_membro_funcao', args=[self.funcao.id, self.membro.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.funcao.membros.filter(id=self.membro.id).exists())
