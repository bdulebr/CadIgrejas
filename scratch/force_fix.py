import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from midia_lgpd.models import PastaVirtual
from core.models import Membro
from gestao_membros.models import Departamento

# Fix members
for membro in Membro.objects.all():
    raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=membro).first()
    if not raiz:
        raiz = PastaVirtual.objects.create(tipo_pasta='usuario', dono_membro=membro, nome=f"Pasta de {membro.first_name}", is_sistema=True)
    
    comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados', dono_membro=membro).first()
    if not comp:
        PastaVirtual.objects.create(tipo_pasta='compartilhados', dono_membro=membro, nome="Compartilhados Comigo", is_sistema=True, parent=raiz)
    else:
        if comp.parent != raiz:
            comp.parent = raiz
            comp.save()

# Fix departments
for dept in Departamento.objects.all():
    raiz = PastaVirtual.objects.filter(tipo_pasta='departamento', departamento=dept).first()
    if not raiz:
        raiz = PastaVirtual.objects.create(tipo_pasta='departamento', departamento=dept, nome=f"Pasta do Departamento: {dept.nome}", is_sistema=True)
    
    comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados', departamento=dept).first()
    if not comp:
        PastaVirtual.objects.create(tipo_pasta='compartilhados', departamento=dept, nome="Arquivos Compartilhados da Equipe", is_sistema=True, parent=raiz)
    else:
        if comp.parent != raiz:
            comp.parent = raiz
            comp.save()

print("FORCED FIX COMPLETE!")
