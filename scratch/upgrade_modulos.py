import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from permissoes.models import ModuloSistema

MODULOS = [
    ('membros', 'Gestão de Membros', 'users'),
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

print("=== INICIANDO UPGRADE DE MÓDULOS DE PERMISSÃO ===")

for slug, nome, icone in MODULOS:
    mod, created = ModuloSistema.objects.get_or_create(
        slug=slug,
        defaults={'nome': nome, 'icone_lucide': icone}
    )
    if created:
        print(f"[NOVO] Módulo registrado: {nome} ({slug})")
    else:
        # Update existing
        mod.nome = nome
        mod.icone_lucide = icone
        mod.save(update_fields=['nome', 'icone_lucide'])
        print(f"[ATUALIZADO] Módulo atualizado: {nome} ({slug})")

print("=== UPGRADE CONCLUÍDO ===")
