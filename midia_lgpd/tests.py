from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from midia_lgpd.models import TermoLGPD, RegistroAceiteLGPD
from gestao_membros.models import Departamento

User = get_user_model()

class LGPDBackendTests(TestCase):
    def setUp(self):
        # Criação de um superuser
        self.user = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123', first_name='Admin'
        )
        self.client = Client()
        self.client.force_login(self.user)

        # Criar os Termos Base
        self.termo_membro = TermoLGPD.objects.create(
            tipo='membro',
            titulo='Termo Membro',
            conteudo_juridico='Texto Membro {{ NOME }} {{ DATA }}',
            is_ativo=True
        )
        self.termo_visitante = TermoLGPD.objects.create(
            tipo='visitante',
            titulo='Termo Visitante',
            conteudo_juridico='Texto Visitante {{ NOME }} {{ CPF }}',
            is_ativo=True
        )
        self.termo_crianca = TermoLGPD.objects.create(
            tipo='crianca',
            titulo='Termo Crianca',
            conteudo_juridico='Texto Crianca',
            is_ativo=True
        )

    def test_model_termo_ativo_unico(self):
        # Garantir que se eu criar um novo termo de visitante ativo, o antigo fica obsoleto
        novo_termo_visitante = TermoLGPD.objects.create(
            tipo='visitante',
            titulo='Novo Termo Visitante',
            conteudo_juridico='Texto Atualizado',
            is_ativo=True
        )
        self.termo_visitante.refresh_from_db()
        self.assertFalse(self.termo_visitante.is_ativo)
        self.assertTrue(novo_termo_visitante.is_ativo)

    def test_db_registro_aceite(self):
        # Teste de inserção manual no banco de dados
        registro = RegistroAceiteLGPD.objects.create(
            nome_completo='Visitante 1',
            cpf='12345678901',
            termo=self.termo_visitante
        )
        self.assertEqual(registro.status, 'pendente')
        self.assertIsNotNone(registro.token_acesso)

    def test_enviar_solicitacao_lgpd_view_ajax(self):
        # Testa a View de envio de solicitação
        url = reverse('enviar_solicitacao_lgpd')
        response = self.client.post(url, {
            'nome_completo': 'Visitante Teste',
            'email': 'teste@pvenseada.org',
            'cpf': '00011122233',
            'tipo_termo': 'visitante'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('sucesso'))
        self.assertIn('lgpd/termo/publico/', data.get('link_publico'))

        # Verifica se foi salvo no DB
        registro = RegistroAceiteLGPD.objects.get(cpf='00011122233')
        self.assertEqual(registro.status, 'pendente')
        self.assertEqual(registro.termo, self.termo_visitante)

    def test_dashboard_painel_render(self):
        # Verifica se o painel carrega com os dados agregados corretos
        RegistroAceiteLGPD.objects.create(nome_completo='V1', termo=self.termo_visitante, status='pendente')
        RegistroAceiteLGPD.objects.create(nome_completo='V2', termo=self.termo_visitante, status='aceito')

        url = reverse('painel_lgpd_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Centro de Compliance LGPD')
        # Verifica se aparecem os Totais
        self.assertContains(response, 'V1')
        self.assertContains(response, 'V2')

class LGPDPublicFrontendTests(TestCase):
    def setUp(self):
        self.termo_visitante = TermoLGPD.objects.create(
            tipo='visitante',
            titulo='Termo Visitante',
            conteudo_juridico='Eu, {{ NOME }}, portador do CPF {{ CPF }}, aceito tudo em {{ DATA }}.',
            is_ativo=True
        )
        self.registro = RegistroAceiteLGPD.objects.create(
            nome_completo='Joao Silva',
            cpf='999.999.999-99',
            termo=self.termo_visitante
        )

    def test_termo_publico_view_render(self):
        url = reverse('termo_publico_view', args=[self.registro.token_acesso])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # O template deve ter injetado o nome e o cpf dinamicamente
        self.assertContains(response, 'Joao Silva')
        self.assertContains(response, '999.999.999-99')
        self.assertContains(response, 'SIM, EU ACEITO')

    def test_processar_aceite_lgpd(self):
        url = reverse('processar_aceite_lgpd', args=[self.registro.token_acesso])
        response = self.client.post(url, {'acao': 'aceito'}, HTTP_X_FORWARDED_FOR='192.168.1.100', HTTP_USER_AGENT='TestAgent')

        # Redireciona de volta
        self.assertEqual(response.status_code, 302)

        # Verifica no DB se os status e metadados foram gravados e PDF gerado
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.status, 'aceito')
        self.assertEqual(self.registro.ip_registro, '192.168.1.100')
        self.assertEqual(self.registro.user_agent, 'TestAgent')
        self.assertTrue(bool(self.registro.arquivo_pdf))
        self.assertTrue(self.registro.arquivo_pdf.name.endswith('.pdf'))

    def test_baixar_pdf_endpoint(self):
        # Aceita para gerar PDF primeiro
        url_aceite = reverse('processar_aceite_lgpd', args=[self.registro.token_acesso])
        self.client.post(url_aceite, {'acao': 'aceito'})

        # Testa o download
        url_download = reverse('baixar_pdf_termo', args=[self.registro.token_acesso])
        response_dl = self.client.get(url_download)
        self.assertEqual(response_dl.status_code, 200)
        self.assertEqual(response_dl['Content-Type'], 'application/pdf')
