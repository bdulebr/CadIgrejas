import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from midia_lgpd.models import PastaVirtual
from core.models import Membro
from gestao_membros.models import Departamento

# Checar quantas pastas Compartilhados existem
count_comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados').count()
print(f"Total Compartilhados: {count_comp}")

# Tentar encontrar a do Marcos Lira (o usuario atual provavelmente é ele)
marcos = Membro.objects.filter(first_name__icontains='Marcos').first()
if marcos:
    print(f"Marcos ID: {marcos.id}")
    raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=marcos).first()
    print(f"Raiz do Marcos: {raiz.id if raiz else 'None'}")
    comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados', dono_membro=marcos).first()
    print(f"Compartilhados do Marcos: {comp.id if comp else 'None'}, Parent: {comp.parent.id if comp and comp.parent else 'None'}")

# Tentar encontrar do Departamento de Almoxarifado
almox = Departamento.objects.filter(nome__icontains='Almox').first()
if almox:
    print(f"Almox ID: {almox.id}")
    raiz_dep = PastaVirtual.objects.filter(tipo_pasta='departamento', departamento=almox).first()
    print(f"Raiz Almox: {raiz_dep.id if raiz_dep else 'None'}")
    comp_dep = PastaVirtual.objects.filter(tipo_pasta='compartilhados', departamento=almox).first()
    print(f"Compartilhados Almox: {comp_dep.id if comp_dep else 'None'}, Parent: {comp_dep.parent.id if comp_dep and comp_dep.parent else 'None'}")

