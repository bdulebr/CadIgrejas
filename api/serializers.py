"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: api/serializers.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""

from rest_framework import serializers
from core.models import Membro
from gestao_membros.models import Departamento, Indisponibilidade, Funcao, ConfiguracaoSlotEscala
from escalas.models import Escala, CompetenciaEscala

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'nome', 'categoria']

class MembroSerializer(serializers.ModelSerializer):
    departamentos = DepartamentoSerializer(source='departamentos_ativos', many=True, read_only=True)
    departamentos_liderados = DepartamentoSerializer(many=True, read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_hierarquico_display', read_only=True)

    class Meta:
        model = Membro
        fields = [
            'id', 'first_name', 'last_name', 'email', 'telefone',
            'nivel_hierarquico', 'nivel_display', 'departamentos', 'departamentos_liderados'
        ]

class EscalaSerializer(serializers.ModelSerializer):
    departamento_nome = serializers.CharField(source='departamento_alocado.nome', read_only=True)
    funcao_nome = serializers.CharField(source='funcao_alocada.nome', read_only=True, default='-')
    tipo_evento_display = serializers.CharField(source='tipo_evento', read_only=True)
    membro_nome = serializers.SerializerMethodField()

    class Meta:
        model = Escala
        fields = ['id', 'data_escala', 'horario_inicio', 'horario_fim', 'tipo_evento_display', 'departamento_nome', 'funcao_nome', 'membro_nome', 'status']

    def get_membro_nome(self, obj):
        return obj.membro_escalado.get_full_name() or obj.membro_escalado.username

class IndisponibilidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indisponibilidade
        fields = ['id', 'data_inicio', 'data_fim', 'motivo', 'criado_em']

class CompetenciaSerializer(serializers.ModelSerializer):
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = CompetenciaEscala
        fields = ['id', 'mes_ano', 'status', 'status_display', 'departamento_nome', 'departamento']

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoSlotEscala
        fields = ['id', 'dia_semana', 'horario_inicio', 'horario_fim', 'tipo_evento', 'quantidade_voluntarios']
