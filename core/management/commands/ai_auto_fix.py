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
from almoxarifado.models import ItemAlmoxarifado
from intranet.services.gemini_ai import consultar_gemini_json
from django.conf import settings

class Command(BaseCommand):
    help = 'Roda o Motor de Automação de IA para encontrar e corrigir inconsistências'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando Motor de Automação de IA...")

        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            self.stderr.write("Erro: API Key do Google Gemini não configurada.")
            return

        anomalias = self._coletar_anomalias()
        if not anomalias:
            self.stdout.write("Nenhuma anomalia encontrada. O banco está saudável.")
            return

        self.stdout.write(f"Anomalias encontradas: {len(anomalias)}. Enviando para a IA...")

        prompt = f"""
        Você é o Motor de Automação e Autocorreção de Banco de Dados da Palavra de Vida Enseada.
        Recebi a seguinte lista de registros anômalos no formato JSON.
        Sua função é propor a correção de cada registro.

        Regras:
        1. Se for 'Item Vencido', mude o 'status_item' para 'consumido' (já que venceu e não está mais disponível).
        2. Para outras anomalias que tenham uma solução lógica direta, informe a correção.

        DADOS DAS ANOMALIAS:
        {json.dumps(anomalias, default=str)}

        Retorne ESTRITAMENTE um JSON no seguinte formato:
        {{
          "acoes": [
            {{"model": "ItemAlmoxarifado", "id": 12, "update": {{"status_item": "consumido"}}}},
            ...
          ]
        }}
        Não retorne nenhum texto markdown, devolva apenas o objeto JSON.
        """

        try:
            texto_limpo = consultar_gemini_json(prompt)
            texto_limpo = texto_limpo.replace('```json', '').replace('```', '').strip()
            resultado = json.loads(texto_limpo)
            acoes = resultado.get("acoes", [])

            self._aplicar_correcoes(acoes)

        except Exception as e:
            self.stderr.write(f"Falha ao processar com IA: {e}")

    def _coletar_anomalias(self):
        dados = []
        hoje = timezone.now().date()
        agora = timezone.now()

        # 1. Itens Vencidos (Almoxarifado)
        try:
            vencidos = ItemAlmoxarifado.objects.filter(data_vencimento__lt=hoje).exclude(status_item__in=['consumido', 'descartado'])
            for v in vencidos:
                dados.append({
                    "tipo": "Item Vencido",
                    "model": "ItemAlmoxarifado",
                    "id": v.id,
                    "nome": v.nome,
                    "validade": str(v.data_vencimento),
                    "status_atual": v.status_item
                })
        except Exception:
            pass

        # 2. Escalas Passadas Pendentes
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

        # 3. Membros Pendentes de Aprovação por muito tempo (> 30 dias)
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

            if not updates:
                continue

            obj = None
            if modelo == "ItemAlmoxarifado":
                obj = ItemAlmoxarifado.objects.filter(id=obj_id).first()
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
