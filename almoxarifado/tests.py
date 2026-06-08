from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models import Membro
from almoxarifado.models import CategoriaItem, ItemAlmoxarifado

@override_settings(AXES_ENABLED=False)
class AlmoxarifadoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = Membro.objects.create_superuser(
            username='admin_almo',
            email='almo@teste.com',
            password='password123',
            cpf='12312312312'
        )
        self.super_admin.nivel_hierarquico = 'super_admin'
        self.super_admin.save()
        self.client.login(username='admin_almo', password='password123')

        # Requires a department to create an asset
        from gestao_membros.models import Departamento
        self.departamento = Departamento.objects.create(nome='TI')

    def test_acesso_painel_almoxarifado(self):
        response = self.client.get(reverse('painel_inventario'))
        self.assertEqual(response.status_code, 200)

    def test_criar_ativo(self):
        categoria = CategoriaItem.objects.create(nome='Móveis')
        response = self.client.post(reverse('cadastrar_item_almoxarifado'), {
            'nome': 'Mesa Som',
            'id_unico': 'PAT001',
            'categoria': categoria.id,
            'status_item': 'disponivel'
        })
        # Note: If validation fails it might return 200 with form errors, if succeeds 302
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ItemAlmoxarifado.objects.filter(id_unico='PAT001').exists())
