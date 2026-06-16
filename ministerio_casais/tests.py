"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: ministerio_casais/tests.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.test import TestCase
from .models import Casal, CursoCasal, MatriculaCursoCasal, HistoricoAconselhamentoCasal, EventoCasal

class MinisterioCasaisModelTests(TestCase):
    def setUp(self):
        self.casal = Casal.objects.create(
            nome_conjuge_1="Marcos",
            nome_conjuge_2="Luana",
            status_relacionamento="Namorados"
        )
        self.curso = CursoCasal.objects.create(
            nome="Curso de Noivos",
            valor_curso=100.00,
            carga_horaria=20
        )
        self.evento = EventoCasal.objects.create(
            titulo="Jantar Romântico",
            data_evento="2026-06-12T20:00:00Z",
            local="Igreja Principal"
        )

    def test_casal_creation_and_properties(self):
        self.assertEqual(self.casal.nomes_juntos, "Marcos e Luana")
        self.assertEqual(self.casal.primeiro_nome_1, "Marcos")
        self.assertEqual(self.casal.primeiro_nome_2, "Luana")
        self.assertEqual(self.casal.status_relacionamento, "Namorados")

    def test_historico_aconselhamento(self):
        historico = HistoricoAconselhamentoCasal.objects.create(
            casal=self.casal,
            pastor_conselheiro="Pastor João",
            observacoes="Sessão de alinhamento",
            nivel_crise=1
        )
        self.assertEqual(historico.casal, self.casal)
        self.assertEqual(historico.nivel_crise, 1)

    def test_matricula_curso(self):
        matricula = MatriculaCursoCasal.objects.create(
            curso=self.curso,
            casal=self.casal,
            status_pagamento="Pago",
            valor_pago=100.00,
            percentual_conclusao=50
        )
        self.assertEqual(matricula.status_pagamento, "Pago")
        self.assertEqual(matricula.percentual_conclusao, 50)
        self.assertFalse(matricula.aprovado)
