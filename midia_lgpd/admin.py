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
