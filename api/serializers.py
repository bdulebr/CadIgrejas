from rest_framework import serializers
from core.models import Membro
from gestao_membros.models import Departamento

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'nome', 'categoria']

class MembroSerializer(serializers.ModelSerializer):
    departamentos = DepartamentoSerializer(source='departamentos_ativos', many=True, read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_hierarquico_display', read_only=True)

    class Meta:
        model = Membro
        fields = [
            'id', 'first_name', 'last_name', 'email', 'telefone', 
            'nivel_hierarquico', 'nivel_display', 'departamentos'
        ]
