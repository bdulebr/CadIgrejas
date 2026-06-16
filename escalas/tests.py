"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: escalas/tests.py
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
from escalas.models import CompetenciaEscala, Escala
from datetime import date, time

@override_settings(AXES_ENABLED=False)
class EscalasTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = Membro.objects.create_superuser(
            username='admin_escalas',
            email='escalas@teste.com',
            password='password123',
            cpf='98765432100'
        )
        self.super_admin.nivel_hierarquico = 'super_admin'
        self.super_admin.save()

        self.membro = Membro.objects.create_user(
            username='membro_escala',
            email='membroescala@teste.com',
            password='password123',
            cpf='11133355577',
            nivel_hierarquico='membro'
        )

        self.departamento = Departamento.objects.create(nome='Louvor')
        self.departamento.membros_ativos.add(self.membro)

        self.client.login(username='admin_escalas', password='password123')

    def test_acesso_painel_escalas(self):
        response = self.client.get(reverse('painel_escalas'))
        self.assertEqual(response.status_code, 200)

    def test_criar_competencia_escala(self):
        response = self.client.post(reverse('nova_competencia'), {
            'departamento_id': self.departamento.id,
            'mes_ano': '10/2026'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CompetenciaEscala.objects.filter(departamento=self.departamento, mes_ano='10/2026').exists())

    def test_adicionar_escala(self):
        competencia = CompetenciaEscala.objects.create(departamento=self.departamento, mes_ano='11/2026')

        # Test creating individual Escala directly on the editor manual endpoint
        response = self.client.post(reverse('salvar_slot_escala', args=[competencia.id]), {
            'membro_id': self.membro.id,
            'data_escala': '2026-11-15',
            'horario_inicio': '19:00',
            'horario_fim': '21:00',
            'tipo_evento': 'culto_domingo',
            'acao': 'add_membro'
        })
        # Could be a redirect or a JSON response or simply re-renders
        # We check the database effect
        escala = Escala.objects.filter(membro_escalado=self.membro, competencia=competencia).first()
        self.assertIsNotNone(escala)
