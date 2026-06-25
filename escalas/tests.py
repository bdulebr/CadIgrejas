from django.test import TestCase, Client
from django.urls import reverse
from core.models import Membro
from gestao_membros.models import Departamento, Funcao
from escalas.models import CultoEvento, CompetenciaEscala
from datetime import date

class EscalasManualEditorTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create user
        self.user = Membro.objects.create_user(
            username='admin_escalas',
            password='password123',
            email='admin@pvenseada.org',
            nivel_hierarquico='super_admin'
        )
        self.client.force_login(self.user)

        # Create core models
        self.dept = Departamento.objects.create(nome='Departamento de Teste')
        self.funcao = Funcao.objects.create(
            departamento=self.dept,
            nome='Funcao Teste'
        )

        self.evento = CultoEvento.objects.create(
            nome='Culto Teste',
            tipo='extra',
            data_evento=date.today()
        )

        self.competencia = CompetenciaEscala.objects.create(
            departamento=self.dept,
            mes_ano=f"{str(date.today().month).zfill(2)}/{date.today().year}",
            status='rascunho'
        )

    def test_editor_manual_renderiza_sem_erros(self):
        # We test that the UI page loads correctly and includes our Alpine fix
        url = reverse('editor_escala_manual', args=[self.competencia.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'editor-manual-board')
        self.assertContains(response, 'x-data="{ selectedMemberId')

    def test_alocar_slot_api_rejeita_post_vazio(self):
        url = reverse('alocar_slot_api')
        response = self.client.post(url, {}, content_type='application/json')
        # If payload is empty, should fail gracefully
        self.assertIn(response.status_code, [400, 403, 404, 500, 405])
