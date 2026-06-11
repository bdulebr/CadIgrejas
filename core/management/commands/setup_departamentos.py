import os
from django.core.management.base import BaseCommand
from gestao_membros.models import Departamento

class Command(BaseCommand):
    help = 'Semeia os departamentos essenciais e de sistema da Intranet.'

    def handle(self, *args, **kwargs):
        deptos_essenciais = [
            {'id_unico_fixo': 'SYS_ALMOX', 'nome': 'Almoxarifado Geral', 'categoria': 'departamento', 'is_system': True},
            {'id_unico_fixo': 'SYS_ESCALAS', 'nome': 'Gestão de Escalas', 'categoria': 'departamento', 'is_system': True},
            {'id_unico_fixo': 'SYS_CRM', 'nome': 'CRM de Visitantes', 'categoria': 'departamento', 'is_system': True},
            {'id_unico_fixo': 'SYS_CASAIS', 'nome': 'Ministério de Casais', 'categoria': 'departamento', 'is_system': True},
            {'id_unico_fixo': 'SYS_ADMIN', 'nome': 'Administração Sysadmin', 'categoria': 'setor', 'is_system': True}
        ]

        criados = 0
        for info in deptos_essenciais:
            obj, created = Departamento.objects.update_or_create(
                id_unico_fixo=info['id_unico_fixo'],
                defaults={
                    'nome': info['nome'],
                    'categoria': info['categoria'],
                    'is_system': info['is_system']
                }
            )
            if created:
                criados += 1
                self.stdout.write(self.style.SUCCESS(f"Departamento criado: {info['nome']}"))
            else:
                self.stdout.write(f"Departamento já existe e foi atualizado: {info['nome']}")

        self.stdout.write(self.style.SUCCESS(f'Semeio concluído. {criados} novos departamentos adicionados.'))
