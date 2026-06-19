"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/signals.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import json
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.middleware import get_current_request
from core.utils_forensics import registrar_log_forense

# Evitar tabelas de controle interno e o próprio log de auditoria
IGNORAR_TABELAS = [
    'LogAuditoria', 'Session', 'AccessAttempt', 'AccessLog',
    'LogEntry', 'ContentType', 'Permission', 'Group', 'Migration'
]

def model_to_dict_safe(instance):
    """Converte um modelo para dicionário de forma segura, evitando erros com campos complexos."""
    try:
        dict_obj = model_to_dict(instance)
        # Sanitizar valores não serializáveis (arquivos, etc)
        for key, value in dict_obj.items():
            if isinstance(value, models.fields.files.FieldFile):
                dict_obj[key] = value.name if value else None
        return dict_obj
    except Exception:
        return {"error": "Não foi possível serializar o objeto."}

@receiver(pre_save)
def auditoria_pre_save(sender, instance, **kwargs):
    if sender.__name__ in IGNORAR_TABELAS:
        return

    # Armazena o estado antigo do objeto se ele já existe no banco
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._estado_antigo = model_to_dict_safe(old_instance)
        except sender.DoesNotExist:
            instance._estado_antigo = {}
    else:
        instance._estado_antigo = {}

@receiver(post_save)
def auditoria_post_save(sender, instance, created, **kwargs):
    if sender.__name__ in IGNORAR_TABELAS:
        return

    try:
        novo_estado = model_to_dict_safe(instance)
        estado_antigo = getattr(instance, '_estado_antigo', {})

        differences = {}
        if created:
            acao = "INSERT"
            differences = novo_estado
        else:
            acao = "UPDATE"
            for key, new_val in novo_estado.items():
                old_val = estado_antigo.get(key)
                if old_val != new_val:
                    differences[key] = {"old": old_val, "new": new_val}

        # Ignorar saves que não alteraram nenhum dado real
        if not differences and not created:
            return

        # Limitar tamanho do JSON para evitar sobrecarga no banco
        diff_str = json.dumps(differences, cls=DjangoJSONEncoder)[:2000]

        request = get_current_request()
        # Se for rotina de background (ex: cronjob), request pode ser None

        registrar_log_forense(
            request=request,
            acao=acao,
            tabela=sender.__name__,
            diff_json=diff_str
        )
    except Exception as e:
        # Se falhar, não podemos parar o sistema de salvar
        print(f"Erro silencioso no LogAuditoria (post_save): {e}")

@receiver(post_delete)
def auditoria_post_delete(sender, instance, **kwargs):
    if sender.__name__ in IGNORAR_TABELAS:
        return

    try:
        estado = model_to_dict_safe(instance)
        diff_str = json.dumps({"deleted_data": estado}, cls=DjangoJSONEncoder)[:2000]

        request = get_current_request()

        registrar_log_forense(
            request=request,
            acao="DELETE",
            tabela=sender.__name__,
            diff_json=diff_str
        )
    except Exception as e:
        print(f"Erro silencioso no LogAuditoria (post_delete): {e}")

from django.db.models.signals import post_migrate

@receiver(post_migrate)
def injetar_templates_padrao(sender, **kwargs):
    if sender.name == 'core':

        # Relatório Almoxarifado

            print("Template 'relatorio_almoxarifado' injetado com sucesso no DB.")

# =========================================================
# CRIAÇÃO AUTOMÁTICA DE PASTAS NO PV DRIVE PARA NOVOS MEMBROS/DEPTOS
# =========================================================

@receiver(post_save, sender='core.Membro')
def criar_pasta_membro_pv_drive(sender, instance, created, **kwargs):
    if created:
        from midia_lgpd.models import PastaVirtual
        try:
            # Cria a pasta raiz do usuário
            pasta_raiz, _ = PastaVirtual.objects.get_or_create(
                tipo_pasta='usuario',
                dono_membro=instance,
                defaults={'nome': f"Pasta de {instance.first_name}", 'is_sistema': True}
            )
            # Cria a pasta de compartilhados do usuário dentro da raiz
            PastaVirtual.objects.get_or_create(
                tipo_pasta='compartilhados',
                dono_membro=instance,
                defaults={'nome': "Compartilhados Comigo", 'is_sistema': True, 'parent': pasta_raiz}
            )
        except Exception as e:
            print(f"Erro ao criar PastaVirtual para Membro {instance.id}: {e}")

@receiver(post_save, sender='gestao_membros.Departamento')
def criar_pasta_depto_pv_drive(sender, instance, created, **kwargs):
    if created:
        from midia_lgpd.models import PastaVirtual
        try:
            # Cria a pasta raiz do departamento
            pasta_raiz, _ = PastaVirtual.objects.get_or_create(
                tipo_pasta='departamento',
                departamento=instance,
                defaults={'nome': f"Pasta do Departamento: {instance.nome}", 'is_sistema': True}
            )
            # Cria a pasta de compartilhados globais do departamento dentro da raiz
            PastaVirtual.objects.get_or_create(
                tipo_pasta='compartilhados',
                departamento=instance,
                defaults={'nome': "Arquivos Compartilhados da Equipe", 'is_sistema': True, 'parent': pasta_raiz}
            )
        except Exception as e:
            print(f"Erro ao criar PastaVirtual para Departamento {instance.id}: {e}")
