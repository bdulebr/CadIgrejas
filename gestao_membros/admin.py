"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: gestao_membros/admin.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
from .models import VagaSetor, CandidaturaVaga, EventoInternoSetor, AnotacaoRH
from .models import AvaliacaoMembro, Ocorrencia, AcaoDisciplinar
from django.contrib import admin
from .models import Departamento, Funcao, Indisponibilidade, AvisoMural, AvisoAnexo, ConfiguracaoSlotEscala

@admin.register(ConfiguracaoSlotEscala)
class ConfiguracaoSlotEscalaAdmin(admin.ModelAdmin):
    list_display = ('departamento', 'funcao', 'quantidade', 'tipo_evento')
    list_filter = ('departamento', 'tipo_evento')
    search_fields = ('departamento__nome', 'funcao__nome')

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'id_unico_fixo')
    list_filter = ('categoria',)
    search_fields = ('nome', 'id_unico_fixo')

@admin.register(Funcao)
class FuncaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nome', 'departamento__nome')

@admin.register(Indisponibilidade)
class IndisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ('membro', 'data_inicio', 'data_fim', 'motivo')
    list_filter = ('data_inicio', 'data_fim')
    search_fields = ('membro__first_name', 'motivo')

@admin.register(AvisoMural)
class AvisoMuralAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'autor', 'data_postagem', 'data_expiracao', 'fixado')
    list_filter = ('fixado', 'departamento', 'data_postagem', 'data_expiracao')
    search_fields = ('titulo', 'mensagem', 'autor__first_name')

@admin.register(AvisoAnexo)
class AvisoAnexoAdmin(admin.ModelAdmin):
    list_display = ('aviso', 'nome_original', 'arquivo')
    search_fields = ('aviso__titulo', 'nome_original')


@admin.register(AvaliacaoMembro)
class AvaliacaoMembroAdmin(admin.ModelAdmin):
    list_display = ('membro', 'avaliador', 'nota', 'data', 'enviado_ao_membro')
    list_filter = ('nota', 'enviado_ao_membro', 'data')
    search_fields = ('membro__first_name', 'avaliador__first_name', 'comentarios')

@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_ocorrencia', 'autor', 'data_registro')
    list_filter = ('data_ocorrencia', 'data_registro')
    search_fields = ('titulo', 'descricao', 'autor__first_name')

@admin.register(AcaoDisciplinar)
class AcaoDisciplinarAdmin(admin.ModelAdmin):
    list_display = ('membro', 'tipo', 'data_aplicacao', 'autor', 'enviado_email')
    list_filter = ('tipo', 'data_aplicacao', 'enviado_email')
    search_fields = ('membro__first_name', 'motivo', 'autor__first_name')


@admin.register(VagaSetor)
class VagaSetorAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'quantidade', 'ativa', 'data_criacao')
    list_filter = ('ativa', 'departamento')
    search_fields = ('titulo', 'departamento__nome')

@admin.register(CandidaturaVaga)
class CandidaturaVagaAdmin(admin.ModelAdmin):
    list_display = ('vaga', 'membro', 'status', 'data_candidatura')
    list_filter = ('status', 'vaga__departamento')
    search_fields = ('membro__first_name', 'vaga__titulo')

@admin.register(EventoInternoSetor)
class EventoInternoSetorAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'data_inicio', 'local')
    list_filter = ('departamento', 'data_inicio')
    search_fields = ('titulo', 'departamento__nome')

@admin.register(AnotacaoRH)
class AnotacaoRHAdmin(admin.ModelAdmin):
    list_display = ('membro', 'autor', 'data_criacao')
    list_filter = ('data_criacao', 'autor')
    search_fields = ('membro__first_name', 'autor__first_name', 'anotacao')
