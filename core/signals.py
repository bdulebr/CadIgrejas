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
