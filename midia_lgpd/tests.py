from django.test import TestCase, Client, override_settings
from django.urls import reverse
from unittest.mock import patch, MagicMock
from core.models import Membro
from gestao_membros.models import Departamento
from midia_lgpd.models import PastaVirtual, PermissaoPVDrive

@override_settings(AXES_ENABLED=False)
class PVDriveTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = Membro.objects.create_superuser(
            username='admin_pv',
            email='pv@teste.com',
            password='password123',
            cpf='33322211100'
        )
        self.super_admin.nivel_hierarquico = 'super_admin'
        self.super_admin.save()
        self.client.login(username='admin_pv', password='password123')

        self.departamento = Departamento.objects.create(nome='TI')

    @patch('midia_lgpd.views.get_drive_service')
    def test_acesso_pv_drive_home(self, mock_get_service):
        mock_get_service.return_value = MagicMock()
        response = self.client.get(reverse('pv_drive_home'))
        self.assertEqual(response.status_code, 302)

    @patch('midia_lgpd.views.get_drive_service')
    def test_criar_pasta_departamento(self, mock_get_service):
        # Mock Google Drive Service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_files = mock_service.files.return_value
        mock_create = mock_files.create.return_value
        mock_create.execute.return_value = {'id': 'mocked_folder_id', 'webViewLink': 'http://mock.link'}

        # Create the parent root folder for the department
        pasta_raiz_dep = PastaVirtual.objects.create(
            nome=self.departamento.nome,
            tipo_pasta='departamento',
            departamento=self.departamento,
            gdrive_folder_id='root_dep_id'
        )

        response = self.client.post(reverse('criar_pasta'), {
            'nome': 'Documentos TI',
            'parent_id': pasta_raiz_dep.id,
            'modo_atual': 'departamento'
        })
        self.assertEqual(response.status_code, 302)

        # Verify db record was created
        pasta = PastaVirtual.objects.filter(nome='Documentos TI', departamento=self.departamento).first()
        self.assertIsNotNone(pasta)
        self.assertEqual(pasta.tipo_pasta, 'normal')
        self.assertEqual(pasta.gdrive_folder_id, 'mocked_folder_id')

    @patch('midia_lgpd.views.get_drive_service')
    def test_criar_pasta_pessoal(self, mock_get_service):
        # Mock Google Drive Service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_files = mock_service.files.return_value
        mock_create = mock_files.create.return_value
        mock_create.execute.return_value = {'id': 'mocked_personal_id', 'webViewLink': 'http://mock.link'}

        # Create personal root folder
        pasta_raiz = PastaVirtual.objects.create(
            nome='Root Pessoal',
            tipo_pasta='usuario',
            dono_membro=self.super_admin,
            gdrive_folder_id='root_mock_id'
        )

        response = self.client.post(reverse('criar_pasta'), {
            'nome': 'Minha Pasta Secreta',
            'parent_id': pasta_raiz.id,
            'modo_atual': 'pessoal'
        })
        self.assertEqual(response.status_code, 302)

        # Verify db record
        pasta = PastaVirtual.objects.filter(nome='Minha Pasta Secreta', dono_membro=self.super_admin).first()
        self.assertIsNotNone(pasta)
        self.assertEqual(pasta.tipo_pasta, 'normal')
