import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from core.models import Membro
from gestao_membros.models import Departamento
from midia_lgpd.models import PastaVirtual

criadas_membros = 0
criadas_deptos = 0
parents_corrigidos = 0

for membro in Membro.objects.all():
    pasta_raiz, _ = PastaVirtual.objects.get_or_create(
        tipo_pasta='usuario',
        dono_membro=membro,
        defaults={'nome': f"Pasta de {membro.first_name}", 'is_sistema': True}
    )
    pasta_compartilhados, created = PastaVirtual.objects.get_or_create(
        tipo_pasta='compartilhados',
        dono_membro=membro,
        defaults={'nome': "Compartilhados Comigo", 'is_sistema': True, 'parent': pasta_raiz}
    )
    if pasta_compartilhados.parent != pasta_raiz:
        pasta_compartilhados.parent = pasta_raiz
        pasta_compartilhados.save()
        parents_corrigidos += 1
    if created: criadas_membros += 1

for dept in Departamento.objects.all():
    pasta_raiz, _ = PastaVirtual.objects.get_or_create(
        tipo_pasta='departamento',
        departamento=dept,
        defaults={'nome': f"Pasta do Departamento: {dept.nome}", 'is_sistema': True}
    )
    pasta_compartilhados, created = PastaVirtual.objects.get_or_create(
        tipo_pasta='compartilhados',
        departamento=dept,
        defaults={'nome': "Arquivos Compartilhados da Equipe", 'is_sistema': True, 'parent': pasta_raiz}
    )
    if pasta_compartilhados.parent != pasta_raiz:
        pasta_compartilhados.parent = pasta_raiz
        pasta_compartilhados.save()
        parents_corrigidos += 1
    if created: criadas_deptos += 1

print(f"Pastas geradas retroativamente: {criadas_membros} membros e {criadas_deptos} departamentos. Parents corrigidos: {parents_corrigidos}.")
