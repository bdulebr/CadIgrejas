from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Membro, LogAuditoria, ConfiguracaoSistema, NoticiaTicker, TemplateDocumento

@admin.register(Membro)
class MembroAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'nivel_hierarquico', 'is_active')
    list_filter = ('nivel_hierarquico', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'cpf')
    readonly_fields = ('hash_aceite_lgpd',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('PV Enseada Dados', {'fields': ('cpf', 'rg', 'telefone', 'foto_perfil', 'data_nascimento', 'data_casamento', 'conjuge', 'filhos', 'habilidades', 'nivel_hierarquico')}),
        ('LGPD', {'fields': ('termos_aceitos', 'hash_aceite_lgpd', 'data_aceite')}),
    )

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario_acao', 'acao_realizada', 'ip_origem', 'cidade_origem', 'tabela_afetada')
    list_filter = ('acao_realizada', 'tabela_afetada', 'data_hora')
    search_fields = ('usuario_acao__first_name', 'hash_atual', 'hash_anterior', 'ip_origem')
    readonly_fields = ('usuario_acao', 'acao_realizada', 'tabela_afetada', 'ip_origem', 'cidade_origem', 'isp_origem', 'user_agent', 'data_hora', 'diferenca_json', 'hash_anterior', 'hash_atual')
    
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('igreja_nome', 'nome_fantasia', 'cnpj', 'is_maintenance', 'ultima_atualizacao')

@admin.register(NoticiaTicker)
class NoticiaTickerAdmin(admin.ModelAdmin):
    list_display = ('texto', 'ativo', 'ordem')
    list_filter = ('ativo',)
    list_editable = ('ativo', 'ordem')
    search_fields = ('texto',)

@admin.register(TemplateDocumento)
class TemplateDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome_acao', 'tipo', 'ativo', 'atualizado_em')
    list_filter = ('tipo', 'ativo')
    search_fields = ('nome_acao', 'assunto_padrao')
