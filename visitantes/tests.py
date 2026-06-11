from django.test import TestCase
from core.models import Membro
from gestao_membros.models import Departamento
from .models import Visitante, VisitaCulto, RegistroAcompanhamento

class VisitantesTestCase(TestCase):
    def setUp(self):
        # Create a mock member
        self.membro = Membro.objects.create_user(
            username='lider_teste',
            email='lider@teste.com',
            password='senha_teste',
            first_name='Líder',
            last_name='Teste',
            cpf='12345678901'
        )

        # Create a mock department
        self.departamento = Departamento.objects.create(
            nome='Recepção',
            categoria='departamento'
        )
        self.departamento.lideres.add(self.membro)

    def test_criar_visitante(self):
        visitante = Visitante.objects.create(
            nome_completo='João Visitante',
            telefone='11999999999',
            tipo='Visitante',
            cadastrado_por=self.membro,
            departamento_responsavel=self.departamento
        )

        self.assertEqual(Visitante.objects.count(), 1)
        self.assertEqual(visitante.nome_completo, 'João Visitante')
        self.assertTrue(visitante.em_acompanhamento)

    def test_registrar_visita_culto(self):
        visitante = Visitante.objects.create(nome_completo='Maria Convertida', tipo='Novo Convertido')

        visita = VisitaCulto.objects.create(
            visitante=visitante,
            observacoes='Veio pela primeira vez após o culto de jovens'
        )

        self.assertEqual(VisitaCulto.objects.count(), 1)
        self.assertEqual(visita.visitante, visitante)

    def test_registro_acompanhamento(self):
        visitante = Visitante.objects.create(nome_completo='Pedro Acompanhado')

        registro = RegistroAcompanhamento.objects.create(
            visitante=visitante,
            meio_contato='WhatsApp',
            responsavel=self.membro,
            resumo_conversa='Conversamos sobre a pregação, ele gostou muito.',
            proximo_passo='Convidar para o GC semana que vem'
        )

        self.assertEqual(RegistroAcompanhamento.objects.count(), 1)
        self.assertEqual(registro.responsavel, self.membro)
        self.assertIn('GC', registro.proximo_passo)
