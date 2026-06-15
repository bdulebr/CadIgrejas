
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .serializers import MembroSerializer, EscalaSerializer, IndisponibilidadeSerializer, CompetenciaSerializer, SlotSerializer
from gestao_membros.models import Indisponibilidade, Departamento, ConfiguracaoSlotEscala
from escalas.models import Escala, CompetenciaEscala
from core.models import Membro, LogImutavel

class PerfilLogadoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(MembroSerializer(request.user).data)

class MinhasEscalasView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        escalas = Escala.objects.filter(membro_escalado=request.user).order_by('data_escala', 'horario_inicio')
        return Response(EscalaSerializer(escalas, many=True).data)

class DepartamentoEscalasView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        deptos = request.user.departamentos_ativos.all()
        escalas = Escala.objects.filter(departamento_alocado__in=deptos).order_by('data_escala', 'horario_inicio')
        return Response(EscalaSerializer(escalas, many=True).data)

class AusenciasView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        ausencias = Indisponibilidade.objects.filter(membro=request.user).order_by('-data_inicio')
        return Response(IndisponibilidadeSerializer(ausencias, many=True).data)

    def post(self, request):
        data = request.data
        try:
            indisp = Indisponibilidade.objects.create(
                membro=request.user,
                data_inicio=data['data_inicio'],
                data_fim=data.get('data_fim', data['data_inicio']),
                motivo=data.get('motivo', 'Não informado')
            )
            LogImutavel.objects.create(membro=request.user, acao='CRIAR_AUSENCIA', dados_acao=f'Ausência de {data["data_inicio"]} até {data.get("data_fim")} - Motivo: {data.get("motivo")}')
            return Response(IndisponibilidadeSerializer(indisp).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LiderMembrosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        deptos = request.user.departamentos_liderados.all()
        membros = Membro.objects.filter(departamentos_ativos__in=deptos).distinct()
        return Response(MembroSerializer(membros, many=True).data)

class LiderCompetenciasView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        deptos = request.user.departamentos_liderados.all()
        comps = CompetenciaEscala.objects.filter(departamento__in=deptos).order_by('-id')
        return Response(CompetenciaSerializer(comps, many=True).data)

    def post(self, request):
        mes_ano = request.data.get('mes_ano')
        depto_id = request.data.get('departamento_id')
        try:
            depto = Departamento.objects.get(id=depto_id, lideres=request.user)
            comp, created = CompetenciaEscala.objects.get_or_create(mes_ano=mes_ano, departamento=depto)
            if created:
                LogImutavel.objects.create(membro=request.user, acao='CRIAR_COMPETENCIA', dados_acao=f'Competencia {mes_ano} para Depto {depto_id}')
            return Response(CompetenciaSerializer(comp).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LiderCompetenciaSlotsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, comp_id):
        try:
            comp = CompetenciaEscala.objects.get(id=comp_id, departamento__lideres=request.user)
            slots = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)
            return Response(SlotSerializer(slots, many=True).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

class MotorIAView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        depto_id = request.data.get('departamento_id')
        try:
            depto = Departamento.objects.get(id=depto_id, lideres=request.user)
            comps = CompetenciaEscala.objects.filter(departamento=depto, is_fechada=False)
            if not comps.exists():
                return Response({'error': 'Nenhuma competência em aberto.'}, status=400)

            comp = comps.first()

            # Simple AI Mock / Offline Fallback logic directly wrapped for API
            from gestao_membros.models import ConfiguracaoSlotEscala
            configuracoes = ConfiguracaoSlotEscala.objects.filter(departamento=comp.departamento)
            if not configuracoes.exists():
                return Response({'error': 'Sem configuração de slot.'}, status=400)

            from django.test import RequestFactory
            from django.contrib.messages.storage.fallback import FallbackStorage
            from escalas.views import gerar_escala_automatica

            # Create a mock request to reuse the existing powerful logic from Django view
            factory = RequestFactory()
            mock_request = factory.post('/fake-url/', {'comp_id': comp.id})
            mock_request.user = request.user
            setattr(mock_request, 'session', 'session')
            messages = FallbackStorage(mock_request)
            setattr(mock_request, '_messages', messages)

            # Call the view
            gerar_escala_automatica(mock_request)
            LogImutavel.objects.create(membro=request.user, acao='ACIONAR_MOTOR_IA', dados_acao=f'Motor IA executado para a competencia {comp.id}')

            # The view redirects, meaning it executed
            return Response({'message': 'Motor de IA acionado. Escala gerada com sucesso!'})

        except Exception as e:
            return Response({'error': str(e)}, status=400)
