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

from .models import PastaVirtual, CompartilhamentoPasta, DocumentoTemplate, DocumentoGerado

@admin.register(PastaVirtual)
class PastaVirtualAdmin(admin.ModelAdmin):
    list_display = ('nome', 'dono', 'parent_folder', 'criado_em')
    search_fields = ('nome', 'dono__first_name')
    list_filter = ('criado_em',)

@admin.register(CompartilhamentoPasta)
class CompartilhamentoPastaAdmin(admin.ModelAdmin):
    list_display = ('pasta', 'membro', 'permissao', 'compartilhado_por')
    list_filter = ('permissao',)

@admin.register(DocumentoTemplate)
class DocumentoTemplateAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'criado_por', 'criado_em')
    search_fields = ('titulo',)

@admin.register(DocumentoGerado)
class DocumentoGeradoAdmin(admin.ModelAdmin):
    list_display = ('template', 'membro_alvo', 'gerado_por', 'data_geracao')
    list_filter = ('data_geracao', 'template')
