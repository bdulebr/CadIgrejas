from django.contrib import admin
from .models import TermoLGPD, AssinaturaLGPD, ArquivoMidia

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

from .models import PastaVirtual, CompartilhamentoPasta, DocumentoTemplate, DocumentoGerado, PermissaoPVDrive

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

@admin.register(DocumentoTemplate)
class DocumentoTemplateAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    search_fields = ('titulo',)

@admin.register(DocumentoGerado)
class DocumentoGeradoAdmin(admin.ModelAdmin):
    list_display = ('template', 'email_destino')
