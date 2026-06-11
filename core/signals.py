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
        from midia_lgpd.models import DocumentoTemplate

        # Relatório Almoxarifado
        if not DocumentoTemplate.objects.filter(identificador_sistema='relatorio_almoxarifado').exists():
            html_almoxarifado = """
            <style>
                body { font-family: Helvetica, sans-serif; }
                h1 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
            <h1>Relatório de Movimentações - Almoxarifado</h1>
            <p>Gerado em: {{ data_geracao|date:"d/m/Y H:i:s" }}</p>
            <table>
                <thead>
                    <tr>
                        <th>Data/Hora</th>
                        <th>Item</th>
                        <th>Tipo</th>
                        <th>Qtd</th>
                        <th>Responsável</th>
                    </tr>
                </thead>
                <tbody>
                    {% for mov in movimentacoes %}
                    <tr>
                        <td>{{ mov.data_hora|date:"d/m/Y H:i" }}</td>
                        <td>{{ mov.item.nome }}</td>
                        <td>{{ mov.get_tipo_display }}</td>
                        <td>{{ mov.quantidade }}</td>
                        <td>{{ mov.responsavel_movimento.get_full_name|default:mov.responsavel_movimento.username }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            """
            DocumentoTemplate.objects.create(
                titulo="Relatório de Almoxarifado Padrão",
                identificador_sistema="relatorio_almoxarifado",
                tipo_documento="pdf_lgpd",
                descricao="Template PDF oficial para o livro razão do Almoxarifado.",
                conteudo_base=html_almoxarifado,
                ativo=True
            )
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
            PastaVirtual.objects.get_or_create(
                tipo_pasta='usuario',
                dono_membro=instance,
                nome=f"Pasta de {instance.first_name}",
                defaults={'is_sistema': True}
            )
            # Cria a pasta de compartilhados do usuário
            PastaVirtual.objects.get_or_create(
                tipo_pasta='compartilhados',
                dono_membro=instance,
                nome="Compartilhados Comigo",
                defaults={'is_sistema': True}
            )
        except Exception as e:
            print(f"Erro ao criar PastaVirtual para Membro {instance.id}: {e}")

@receiver(post_save, sender='gestao_membros.Departamento')
def criar_pasta_depto_pv_drive(sender, instance, created, **kwargs):
    if created:
        from midia_lgpd.models import PastaVirtual
        try:
            # Cria a pasta raiz do departamento
            PastaVirtual.objects.get_or_create(
                tipo_pasta='departamento',
                departamento=instance,
                nome=f"Pasta do Departamento: {instance.nome}",
                defaults={'is_sistema': True}
            )
            # Cria a pasta de compartilhados globais do departamento
            PastaVirtual.objects.get_or_create(
                tipo_pasta='compartilhados',
                departamento=instance,
                nome="Arquivos Compartilhados da Equipe",
                defaults={'is_sistema': True}
            )
        except Exception as e:
            print(f"Erro ao criar PastaVirtual para Departamento {instance.id}: {e}")
