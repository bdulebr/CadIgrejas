from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Membro, LogAuditoria, ConfiguracaoSistema, NoticiaTicker

@admin.register(Membro)
class MembroAdmin(UserAdmin):
    list_display = ('username', 'apelido', 'email', 'first_name', 'last_name', 'nivel_hierarquico', 'is_active')
    list_filter = ('nivel_hierarquico', 'is_active', 'is_staff')
    search_fields = ('username', 'apelido', 'email', 'first_name', 'last_name', 'cpf')
    readonly_fields = ('hash_aceite_lgpd',)

    fieldsets = UserAdmin.fieldsets + (
        ('PV Enseada Dados', {'fields': (
            'apelido', 'cpf', 'rg', 'telefone', 'foto_perfil', 'data_nascimento', 'data_casamento',
            'conjuge', 'filhos', 'sexo', 'estado_civil', 'profissao', 'escolaridade',
            'habilidades', 'nivel_hierarquico', 'status_conta', 'anotacoes_lideranca'
        )}),
        ('Endereço', {'fields': (
            'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado'
        )}),
        ('Eclesiástico', {'fields': (
            'data_batismo', 'membro_desde', 'igreja_anterior'
        )}),
        ('Extras', {'fields': (
            'redes_sociais', 'tamanho_camisa', 'alergias', 'contato_emergencia'
        )}),
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

from .models import LinkRapido

@admin.register(LinkRapido)
class LinkRapidoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'url', 'ordem')
    search_fields = ('titulo', 'url')
    ordering = ('ordem',)

from .models import NotificacaoGlobal
@admin.register(NotificacaoGlobal)
class NotificacaoGlobalAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'destinatario', 'tipo', 'lida', 'data_criacao')
    list_filter = ('lida', 'tipo', 'data_criacao')
    search_fields = ('titulo', 'mensagem', 'destinatario__username', 'destinatario__first_name')

from .models import EmailLog

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('destinatario', 'assunto', 'status', 'data_envio')
    list_filter = ('status', 'data_envio')
    search_fields = ('destinatario', 'assunto')
