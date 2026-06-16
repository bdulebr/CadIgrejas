"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/rotina_meia_noite.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from almoxarifado.models import AlimentoLote
from gestao_membros.models import AvisoMural, Departamento
from core.models import Membro
from django.utils import timezone

class Command(BaseCommand):
    help = 'Executa a rotina de manutenção diária pós-meia-noite.'

    def handle(self, *args, **kwargs):
        self.stdout.write("==================================================")
        self.stdout.write(f"Iniciando Rotina Pós-Meia-Noite - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.stdout.write("==================================================")

        # 1. Acionar o Backup Automático
        self.stdout.write("\n[1] Iniciando módulo de Backup DB...")
        try:
            call_command('backup_db')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao executar backup: {e}"))

        # 2. Verificação de Validades do Almoxarifado (Aviso de Vencimento de Consumíveis)
        self.stdout.write("\n[2] Verificando validades no Almoxarifado...")
        try:
            daqui_7_dias = timezone.now().date() + datetime.timedelta(days=7)
            lotes_vencendo = AlimentoLote.objects.filter(
                data_vencimento__lte=daqui_7_dias,
                quantidade_atual__gt=0
            )

            if lotes_vencendo.exists():
                admin_bot = Membro.objects.filter(is_superuser=True).first()
                if admin_bot:
                    for lote in lotes_vencendo:
                        if lote.departamento:
                            titulo = f"ALERTA: Lote Vencendo ({lote.nome})"
                            mensagem = f"Atenção equipe! O lote de '{lote.nome}' ({lote.quantidade_atual} un) está próximo do vencimento (Vence dia: {lote.data_vencimento.strftime('%d/%m/%Y')}). Por favor, priorize o consumo ou doação imediata."

                            # Evitar flood de avisos repetidos
                            aviso_existente = AvisoMural.objects.filter(
                                departamento=lote.departamento,
                                titulo=titulo,
                                data_postagem__gte=timezone.now() - datetime.timedelta(days=1)
                            ).exists()

                            if not aviso_existente:
                                AvisoMural.objects.create(
                                    departamento=lote.departamento,
                                    autor=admin_bot,
                                    titulo=titulo,
                                    mensagem=mensagem,
                                    fixado=True
                                )
                                self.stdout.write(f"  -> Aviso criado para {lote.nome} no dpt {lote.departamento.nome}")
                self.stdout.write(self.style.SUCCESS(f"Avisos gerados para {lotes_vencendo.count()} lote(s) vencendo."))
            else:
                self.stdout.write("Nenhum lote perto de vencer.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao verificar almoxarifado: {e}"))

        self.stdout.write("\n==================================================")
        self.stdout.write("Rotina Pós-Meia-Noite concluída com sucesso.")
        self.stdout.write("==================================================")
