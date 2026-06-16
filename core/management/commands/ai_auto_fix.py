"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/ai_auto_fix.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import json
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Membro, LogAuditoria
from almoxarifado.models import AlimentoLote, Emprestimo
from intranet.services.groq_ai import obter_client_groq

class Command(BaseCommand):
    help = 'Roda o Motor de Automação de IA para encontrar e corrigir inconsistências'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando Motor de Automação de IA...")

        client = obter_client_groq()
        if not client:
            self.stderr.write("Erro: API Key do Groq não configurada.")
            return

        anomalias = self._coletar_anomalias()
        if not anomalias:
            self.stdout.write("Nenhuma anomalia encontrada. O banco está saudável.")
            return

        self.stdout.write(f"Anomalias encontradas: {len(anomalias)}. Enviando para a IA...")

        prompt = """
        Você é o Motor de Automação e Autocorreção de Banco de Dados da Palavra de Vida Enseada.
        Recebi a seguinte lista de registros anômalos no formato JSON.
        Sua função é propor a correção de cada registro.

        Regras:
        1. Se for 'Alimento Vencido', mude o 'status' para 'Vencido'.
        2. Se for 'Empréstimo Atrasado', você pode mudar o 'status' para 'Atrasado' (se aplicável).
        3. Para outras anomalias que tenham uma solução lógica direta, informe a correção.

        Retorne ESTRITAMENTE um JSON no seguinte formato (uma lista de dicionários):
        [
          {"model": "AlimentoLote", "id": 12, "update": {"status": "Vencido"}},
          ...
        ]
        Não retorne nenhum texto markdown (como ```json), devolva apenas a string JSON crua.
        """

        try:
            response = client.models.generate_content(
                model='llama-3.3-70b-versatile',
                contents=[json.dumps(anomalias, default=str), prompt]
            )

            texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
            acoes = json.loads(texto_limpo)

            self._aplicar_correcoes(acoes)

        except Exception as e:
            self.stderr.write(f"Falha ao processar com IA: {e}")

    def _coletar_anomalias(self):
        dados = []
        hoje = timezone.now().date()
        agora = timezone.now()

        # 1. Alimentos Vencidos
        try:
            vencidos = AlimentoLote.objects.filter(data_validade__lt=hoje).exclude(status__in=['Vencido', 'Consumido'])
            for v in vencidos:
                dados.append({
                    "tipo": "Alimento Vencido",
                    "model": "AlimentoLote",
                    "id": v.id,
                    "nome": v.alimento.nome,
                    "validade": str(v.data_validade),
                    "status_atual": getattr(v, 'status', 'N/A')
                })
        except Exception:
            pass

        # 2. Empréstimos Atrasados
        try:
            atrasados = Emprestimo.objects.filter(data_devolucao_prevista__lt=hoje, data_devolucao_real__isnull=True)
            for a in atrasados:
                dados.append({
                    "tipo": "Empréstimo Atrasado",
                    "model": "Emprestimo",
                    "id": a.id,
                    "data_prevista": str(a.data_devolucao_prevista),
                    "status_atual": getattr(a, 'status', 'N/A')
                })
        except Exception:
            pass

        # 3. Escalas Passadas Pendentes
        try:
            from escalas.models import Escala
            escalas_pendentes = Escala.objects.filter(data_escala__lt=hoje, status='Aguardando')
            for e in escalas_pendentes:
                dados.append({
                    "tipo": "Escala Passada Pendente",
                    "model": "Escala",
                    "id": e.id,
                    "data_escala": str(e.data_escala),
                    "status_atual": e.status
                })
        except Exception:
            pass

        # 4. Membros Pendentes de Aprovação por muito tempo (> 30 dias)
        try:
            limite_aprovacao = agora - datetime.timedelta(days=30)
            membros_esquecidos = Membro.objects.filter(is_active=False, date_joined__lt=limite_aprovacao)
            for m in membros_esquecidos:
                dados.append({
                    "tipo": "Membro Esquecido",
                    "model": "Membro",
                    "id": m.id,
                    "data_cadastro": str(m.date_joined),
                    "is_active": m.is_active
                })
        except Exception:
            pass

        return dados

    def _aplicar_correcoes(self, acoes):
        # Para loggar quem fez, criamos um dummy ou pegamos superadmin,
        # mas LogAuditoria aceita usuario_acao nulo com descricao
        for acao in acoes:
            modelo = acao.get("model")
            obj_id = acao.get("id")
            updates = acao.get("update", {})

            if not updates: continue

            obj = None
            if modelo == "AlimentoLote":
                obj = AlimentoLote.objects.filter(id=obj_id).first()
            elif modelo == "Emprestimo":
                obj = Emprestimo.objects.filter(id=obj_id).first()
            elif modelo == "Escala":
                from escalas.models import Escala
                obj = Escala.objects.filter(id=obj_id).first()
            elif modelo == "Membro":
                obj = Membro.objects.filter(id=obj_id).first()

            if obj:
                diferenca = {"antes": {}, "depois": {}}
                for k, v in updates.items():
                    if hasattr(obj, k):
                        diferenca["antes"][k] = getattr(obj, k)
                        setattr(obj, k, v)
                        diferenca["depois"][k] = v

                obj.save()

                LogAuditoria.objects.create(
                    usuario_acao=None,  # Ação do sistema
                    acao_realizada="AI_AUTO_CORRECTION",
                    tabela_afetada=modelo,
                    diferenca_json={"anomalia_detectada": "Sim", "correcoes": diferenca}
                )
                self.stdout.write(f"Corrigido {modelo} ID {obj_id} via IA.")
