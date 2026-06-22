import os
import sys
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from permissoes.models import ModuloSistema

modulos = [
    {'nome': 'Gestão de Membros', 'slug': 'membros', 'icone_lucide': 'users'},
    {'nome': 'Tesouraria', 'slug': 'tesouraria', 'icone_lucide': 'wallet'},
    {'nome': 'Gestão de Escalas', 'slug': 'escalas', 'icone_lucide': 'calendar'},
    {'nome': 'Almoxarifado', 'slug': 'almoxarifado', 'icone_lucide': 'box'},
    {'nome': 'Ministério de Casais', 'slug': 'casais', 'icone_lucide': 'heart'},
    {'nome': 'Visitantes (CRM)', 'slug': 'visitantes', 'icone_lucide': 'user-plus'},
    {'nome': 'Mídia & LGPD', 'slug': 'midia', 'icone_lucide': 'camera'},
    {'nome': 'PDV', 'slug': 'pdv', 'icone_lucide': 'shopping-cart'},
    {'nome': 'Administração do Sistema', 'slug': 'sysadmin', 'icone_lucide': 'settings'},
    {'nome': 'Permissões e Acessos', 'slug': 'permissoes', 'icone_lucide': 'shield'},
]

for mod in modulos:
    obj, created = ModuloSistema.objects.get_or_create(
        slug=mod['slug'],
        defaults={'nome': mod['nome'], 'icone_lucide': mod['icone_lucide']}
    )
    if created:
        print(f"Módulo criado: {mod['nome']}")
    else:
        obj.nome = mod['nome']
        obj.icone_lucide = mod['icone_lucide']
        obj.save()
        print(f"Módulo atualizado: {mod['nome']}")

print("Semeio de Módulos concluído com sucesso!")
