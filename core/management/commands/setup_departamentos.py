import os
from django.core.management.base import BaseCommand
from gestao_membros.models import Departamento

class Command(BaseCommand):
    help = 'Semeia os departamentos essenciais da Intranet.'

    def handle(self, *args, **kwargs):
        deptos_essenciais = [
            {'nome': 'Almoxarifado Geral', 'categoria': 'departamento'},
            {'nome': 'Gestão de Escalas', 'categoria': 'departamento'},
            {'nome': 'Administração Sysadmin', 'categoria': 'setor'}
        ]
        
        criados = 0
        for info in deptos_essenciais:
            obj, created = Departamento.objects.get_or_create(
                nome=info['nome'],
                defaults={'categoria': info['categoria']}
            )
            if created:
                criados += 1
                self.stdout.write(self.style.SUCCESS(f"Departamento criado: {info['nome']}"))
            else:
                self.stdout.write(f"Departamento já existe: {info['nome']}")
                
        self.stdout.write(self.style.SUCCESS(f'Semeio concluído. {criados} departamentos adicionados.'))
