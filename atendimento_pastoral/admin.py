"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: atendimento_pastoral/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
"""
from .models import SessaoAtendimento, AgendamentoPastoral, PessoaAtendimento
from django.contrib import admin

# Register your models here.


@admin.register(PessoaAtendimento)
class PessoaAtendimentoAdmin(admin.ModelAdmin):
    pass

@admin.register(AgendamentoPastoral)
class AgendamentoPastoralAdmin(admin.ModelAdmin):
    pass

@admin.register(SessaoAtendimento)
class SessaoAtendimentoAdmin(admin.ModelAdmin):
    pass
