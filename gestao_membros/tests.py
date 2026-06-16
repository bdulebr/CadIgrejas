"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/tests.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models import Membro
from gestao_membros.models import Departamento

@override_settings(AXES_ENABLED=False)
class GestaoMembrosTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a Super Admin to bypass auth limits
        self.super_admin = Membro.objects.create_superuser(
            username='admin_teste',
            email='admin@teste.com',
            password='password123',
            cpf='11122233344',
            telefone='11999999999'
        )
        self.super_admin.nivel_hierarquico = 'super_admin'
        self.super_admin.save()

        # Create a basic member
        self.membro = Membro.objects.create_user(
            username='membro_teste',
            email='membro@teste.com',
            password='password123',
            cpf='55566677788',
            nivel_hierarquico='membro'
        )

    def test_acesso_painel_membros_admin(self):
        self.client.login(username='admin_teste', password='password123')
        response = self.client.get(reverse('painel_membros'))
        self.assertEqual(response.status_code, 200)

    def test_acesso_painel_membros_membro_comum_vazio(self):
        self.client.login(username='membro_teste', password='password123')
        response = self.client.get(reverse('painel_membros'))
        # Should render 200, but have 0 members since not a leader
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['membros']), 0)

    def test_criar_departamento(self):
        self.client.login(username='admin_teste', password='password123')
        response = self.client.post(reverse('departamentos'), {
            'nome': 'Departamento Teste',
            'categoria': 'Geral'
        })
        self.assertEqual(response.status_code, 200) # Since it just renders the page again
        self.assertTrue(Departamento.objects.filter(nome='Departamento Teste').exists())

    def test_editar_departamento(self):
        dep = Departamento.objects.create(nome='Antigo')
        self.client.login(username='admin_teste', password='password123')
        response = self.client.post(reverse('detalhes_departamento', args=[dep.id]), {
            'acao': 'editar',
            'nome': 'Novo Nome',
            'categoria': 'Geral'
        })
        self.assertEqual(response.status_code, 302)
        dep.refresh_from_db()
        self.assertEqual(dep.nome, 'Novo Nome')

    def test_vincular_membro_departamento(self):
        dep = Departamento.objects.create(nome='Dep Membros')
        self.client.login(username='admin_teste', password='password123')
        response = self.client.post(reverse('atribuir_lideranca', args=[dep.id]), {
            'membro_id': self.membro.id,
            'acao': 'add_membro'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(dep.membros_ativos.filter(id=self.membro.id).exists())
