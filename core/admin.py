"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import LogImutavel, AIEngineerLog, Membro, LogAuditoria, ConfiguracaoSistema, NoticiaTicker, LinkRapido, NotificacaoGlobal, EmailLog, DatabaseBackup, SpiderTestLog, AlertaInvasao, LogWhatsApp

@admin.register(Membro)
class MembroAdmin(UserAdmin):
    list_display = ('username', 'apelido', 'email', 'first_name', 'last_name', 'nivel_hierarquico', 'is_active')
    list_filter = ('nivel_hierarquico', 'is_active', 'is_staff')
    search_fields = ('username', 'apelido', 'email', 'first_name', 'last_name', 'cpf')
    readonly_fields = ('hash_aceite_lgpd',)

    fieldsets = UserAdmin.fieldsets + (
        ('PV Enseada Dados', {'fields': (
            'apelido', 'cpf', 'rg', 'telefone', 'foto_perfil', 'data_nascimento', 'data_casamento',
            'conjuge', 'filhos', 'sexo', 'estado_civil', 'profissao', 'escolaridade'
        )}),
        ('Permissões e Vínculos', {
            'fields': (
                'nivel_hierarquico', 'status_conta'
            )
        }),
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
    list_display = ('titulo', 'ativo', 'ordem')
    list_filter = ('ativo',)
    list_editable = ('ativo', 'ordem')
    search_fields = ('titulo', 'mensagem')

@admin.register(LinkRapido)
class LinkRapidoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'url', 'ordem')
    search_fields = ('titulo', 'url')
    ordering = ('ordem',)

@admin.register(NotificacaoGlobal)
class NotificacaoGlobalAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'destinatario', 'tipo', 'lida', 'data_criacao')
    list_filter = ('lida', 'tipo', 'data_criacao')
    search_fields = ('titulo', 'mensagem', 'destinatario__username', 'destinatario__first_name')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('destinatario', 'assunto', 'status', 'data_envio')
    list_filter = ('status', 'data_envio')
    search_fields = ('destinatario', 'assunto')
    readonly_fields = ('data_envio',)

@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ('arquivo', 'data_criacao', 'tamanho_mb')
    list_filter = ('data_criacao',)
    readonly_fields = ('data_criacao',)

@admin.register(SpiderTestLog)
class SpiderTestLogAdmin(admin.ModelAdmin):
    list_display = ('data_execucao', 'iniciado_por', 'total_urls', 'erros_encontrados')
    list_filter = ('data_execucao',)
    search_fields = ('log_texto',)
    readonly_fields = ('data_execucao',)


@admin.register(AIEngineerLog)
class AIEngineerLogAdmin(admin.ModelAdmin):
    pass

@admin.register(LogImutavel)
class LogImutavelAdmin(admin.ModelAdmin):
    pass

@admin.register(AlertaInvasao)
class AlertaInvasaoAdmin(admin.ModelAdmin):
    list_display = ('ip', 'membro', 'caminho_url', 'data_hora', 'resolvido')
    search_fields = ('ip',)

@admin.register(LogWhatsApp)
class LogWhatsAppAdmin(admin.ModelAdmin):
    list_display = ('destinatario_numero', 'status', 'data_envio')
    search_fields = ('destinatario_numero',)
