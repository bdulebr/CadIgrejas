"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: midia_lgpd/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from .models import PastaVirtual, CompartilhamentoPasta, PermissaoPVDrive
from django.contrib import admin
from .models import TermoLGPD, AssinaturaLGPD, ArquivoMidia, RegistroAceiteLGPD

@admin.register(RegistroAceiteLGPD)
class RegistroAceiteLGPDAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'cpf', 'status', 'data_solicitacao')
    list_filter = ('status',)
    search_fields = ('nome_completo', 'cpf', 'ip_registro')

@admin.register(TermoLGPD)
class TermoLGPDAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_publicacao', 'is_ativo')
    list_filter = ('is_ativo', 'data_publicacao')
    search_fields = ('titulo',)

@admin.register(AssinaturaLGPD)
class AssinaturaLGPDAdmin(admin.ModelAdmin):
    list_display = ('membro', 'termo', 'data_aceite', 'ip_registro')
    list_filter = ('data_aceite', 'termo')
    search_fields = ('membro__first_name',)

@admin.register(ArquivoMidia)
class ArquivoMidiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'data_envio', 'enviado_por')
    list_filter = ('departamento', 'data_envio', 'is_publico_para_membros')
    search_fields = ('titulo', 'enviado_por__first_name')


@admin.register(PastaVirtual)
class PastaVirtualAdmin(admin.ModelAdmin):
    list_display = ('nome', 'departamento', 'gdrive_folder_id')
    search_fields = ('nome',)

@admin.register(PermissaoPVDrive)
class PermissaoPVDriveAdmin(admin.ModelAdmin):
    list_display = ('pasta', 'alvo_departamento', 'alvo_membro', 'nivel', 'validade', 'is_ativo')
    list_filter = ('nivel', 'is_ativo', 'alvo_departamento')

@admin.register(CompartilhamentoPasta)
class CompartilhamentoPastaAdmin(admin.ModelAdmin):
    list_display = ('pasta', 'departamento_destino')
