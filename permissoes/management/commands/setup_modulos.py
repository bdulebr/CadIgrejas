from django.core.management.base import BaseCommand
from permissoes.models import ModuloSistema

class Command(BaseCommand):
    help = 'Registra ou atualiza os módulos do sistema para controle de permissões (RBAC)'

    def handle(self, *args, **kwargs):
        MODULOS = [
            ('membros', 'Gestão de Membros', 'users'),
            ('rh', 'Recursos Humanos', 'users-cog'),
            ('tesouraria', 'Tesouraria', 'wallet'),
            ('escalas', 'Gestão de Escalas', 'calendar'),
            ('almoxarifado', 'Almoxarifado', 'box'),
            ('casais', 'Ministério de Casais', 'heart-handshake'),
            ('visitantes', 'Visitantes (CRM)', 'contact-2'),
            ('midia', 'Mídia & LGPD', 'shield-check'),
            ('pv_drive', 'PV Drive (Arquivos)', 'cloud'),
            ('pdv', 'PDV (Gestão de Caixa)', 'shopping-cart'),
            ('sysadmin', 'Administração do Sistema', 'server'),
            ('permissoes', 'Permissões e Acessos', 'shield'),
            ('atendimento_pastoral', 'Gabinete Pastoral', 'book-open'),
        ]

        self.stdout.write(self.style.WARNING("=== INICIANDO UPGRADE DE MÓDULOS DE PERMISSÃO ==="))

        for slug, nome, icone in MODULOS:
            mod, created = ModuloSistema.objects.get_or_create(
                slug=slug,
                defaults={'nome': nome, 'icone_lucide': icone}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"[NOVO] Módulo registrado: {nome} ({slug})"))
            else:
                mod.nome = nome
                mod.icone_lucide = icone
                mod.save(update_fields=['nome', 'icone_lucide'])
                self.stdout.write(self.style.SUCCESS(f"[ATUALIZADO] Módulo atualizado: {nome} ({slug})"))

        self.stdout.write(self.style.SUCCESS("=== UPGRADE CONCLUÍDO ==="))
