"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: permissoes/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from django.contrib import admin
from .models import ModuloSistema, PerfilAcesso, PermissaoMembro, PermissaoDepartamento, PermissaoPerfil

admin.site.register(ModuloSistema)
admin.site.register(PerfilAcesso)

class PermissaoBaseAdmin(admin.ModelAdmin):
    list_display = ('modulo', 'pode_ver', 'pode_editar', 'pode_excluir', 'escopo_acesso', 'data_expiracao')
    list_filter = ('modulo', 'escopo_acesso')
    search_fields = ('modulo__nome',)

@admin.register(PermissaoMembro)
class PermissaoMembroAdmin(PermissaoBaseAdmin):
    list_display = ('membro',) + PermissaoBaseAdmin.list_display
    search_fields = ('membro__first_name', 'modulo__nome')

@admin.register(PermissaoDepartamento)
class PermissaoDepartamentoAdmin(PermissaoBaseAdmin):
    list_display = ('departamento',) + PermissaoBaseAdmin.list_display
    search_fields = ('departamento__nome', 'modulo__nome')

@admin.register(PermissaoPerfil)
class PermissaoPerfilAdmin(PermissaoBaseAdmin):
    list_display = ('perfil',) + PermissaoBaseAdmin.list_display
    search_fields = ('perfil__nome', 'modulo__nome')
