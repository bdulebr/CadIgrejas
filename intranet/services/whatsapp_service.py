"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/services/whatsapp_service.py
* DESCRIÇÃO: Motor Avançado de envio de mensagens via Meta Cloud API (WhatsApp)
* INSPIRAÇÃO: Mesquita Assessoria Contábil API
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.3
* DATA DA ÚLTIMA ALTERAÇÃO: 22/06/2026
"""
import requests
import json
import re
from django.conf import settings
from django.template.loader import render_to_string

def sanitize_phone_number(numero):
    """
    Higieniza o número removendo espaços, traços, parênteses e forçando DDI 55 se ausente.
    """
    if not numero:
        return ""
    # Remove tudo que não for dígito
    limpo = re.sub(r'\D', '', str(numero))
    if not limpo:
        return ""

    # Se o número tiver 10 ou 11 dígitos, provavelmente é BR sem o 55
    if len(limpo) in [10, 11]:
        limpo = f"55{limpo}"

    return limpo

class WhatsAppClient:
    def __init__(self):
        from core.models import ConfiguracaoSistema
        config = ConfiguracaoSistema.objects.first()

        self.is_active = config.whatsapp_ativo if config else False
        self.access_token = config.whatsapp_access_token if config else ""
        self.phone_number_id = config.whatsapp_phone_number_id if config else ""
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def _check_status(self, to):
        if not self.is_active:
            print(f"[WhatsApp PAUSADO - MASTER SWITCH OFF] Para: {to}")
            return False
        if not self.access_token or not self.phone_number_id:
            print("[WhatsApp FALHA] Credenciais não configuradas no painel Sysadmin.")
            return False
        return True

    def _execute_request(self, payload: dict, to: str, template_usado: str) -> dict:
        """
        Executa o request para a Meta API e sempre registra no LogWhatsApp.
        """
        from core.models import LogWhatsApp

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Tenta executar
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            status_code = response.status_code
            resp_json = response.json()

            sucesso = status_code in [200, 201]

            # Registra no Log
            LogWhatsApp.objects.create(
                destinatario_numero=to,
                template_usado=template_usado,
                corpo_json=json.dumps(payload),
                status='enviado' if sucesso else 'falha',
                erro_mensagem=None if sucesso else str(resp_json)
            )

            if sucesso:
                print(f"[WhatsApp Real Enviado] Para: {to} | Template: {template_usado}")
            else:
                print(f"[WhatsApp API Erro] Para: {to} | Erro: {resp_json}")

            return {"status_code": status_code, "response": resp_json}

        except Exception as e:
            print(f"[FALHA EXTREMA WHATSAPP] Erro: {str(e)}")
            LogWhatsApp.objects.create(
                destinatario_numero=to,
                template_usado=template_usado,
                corpo_json=json.dumps(payload),
                status='falha',
                erro_mensagem=str(e)
            )
            return {"error": str(e)}

    def send_text(self, to: str, body: str, template_usado: str = "Texto Livre") -> dict:
        to_clean = sanitize_phone_number(to)
        if not self._check_status(to_clean):
            return {"error": "Servico pausado ou sem credenciais"}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body
            }
        }
        return self._execute_request(payload, to_clean, template_usado)

    def send_document(self, to: str, document_url: str, filename: str = "documento.pdf") -> dict:
        to_clean = sanitize_phone_number(to)
        if not self._check_status(to_clean):
            return {"error": "Servico pausado ou sem credenciais"}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        return self._execute_request(payload, to_clean, "Documento PDF")

    def send_button_message(self, to: str, body: str, buttons: list) -> dict:
        to_clean = sanitize_phone_number(to)
        if not self._check_status(to_clean):
            return {"error": "Servico pausado ou sem credenciais"}

        buttons_payload = []
        for i, btn_text in enumerate(buttons[:3]):
            buttons_payload.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": btn_text
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body
                },
                "action": {
                    "buttons": buttons_payload
                }
            }
        }
        return self._execute_request(payload, to_clean, "Botões Interativos")


def enviar_whatsapp_template(destinatario_numero, template_name, context):
    """
    Renderiza um template de texto (.txt ou .html sem tags) e envia como mensagem de texto.
    Isso simula de forma fictícia os templates estruturados da Meta.
    """
    if not destinatario_numero:
        return False

    try:
        # Tenta renderizar
        corpo_texto = render_to_string(f"whatsapp/{template_name}", context)
        # Limpa tags HTML se houver (caso passem um template html por engano)
        from django.utils.html import strip_tags
        corpo_texto = strip_tags(corpo_texto).strip()

        client = WhatsAppClient()
        result = client.send_text(destinatario_numero, corpo_texto, template_usado=template_name)
        return result.get('status_code') in [200, 201]
    except Exception as e:
        print(f"[Erro Renderização Template WhatsApp] {e}")
        # Loga a falha
        from core.models import LogWhatsApp
        LogWhatsApp.objects.create(
            destinatario_numero=destinatario_numero,
            template_usado=template_name,
            status='falha',
            erro_mensagem=f"Falha na renderização do template: {str(e)}"
        )
        return False

def reenviar_whatsapp_falho(log_id):
    """
    Tenta reenviar um WhatsApp que falhou, recuperando seu payload original JSON.
    """
    from core.models import LogWhatsApp

    try:
        log = LogWhatsApp.objects.get(id=log_id, status='falha')
    except LogWhatsApp.DoesNotExist:
        return False, "Log de WhatsApp não encontrado ou já enviado."

    client = WhatsAppClient()
    if not client.is_active:
        return False, "Envios de WhatsApp estão pausados pelo SysAdmin."

    if not log.corpo_json:
        return False, "O payload JSON não foi salvo para esta mensagem. Impossível reenviar."

    log.qtd_reenvios += 1
    log.save()

    try:
        payload = json.loads(log.corpo_json)

        headers = {
            "Authorization": f"Bearer {client.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(client.base_url, headers=headers, json=payload, timeout=10)

        if response.status_code in [200, 201]:
            log.status = 'enviado'
            log.erro_mensagem = None
            log.save()
            return True, "WhatsApp reenviado com sucesso!"
        else:
            log.erro_mensagem = str(response.json())
            log.save()
            return False, f"Falha da API: {response.json()}"

    except Exception as e:
        log.erro_mensagem = str(e)
        log.save()
        return False, f"Falha local no reenvio: {str(e)}"

# Wrappers Antigos (Para manter compatibilidade)
def enviar_whatsapp_mensagem(destinatario_numero, mensagem):
    client = WhatsAppClient()
    result = client.send_text(destinatario_numero, mensagem)
    return result.get('status_code') in [200, 201]

def enviar_whatsapp_pdf(destinatario_numero, arquivo_url, filename="documento.pdf"):
    client = WhatsAppClient()
    result = client.send_document(destinatario_numero, arquivo_url, filename)
    return result.get('status_code') in [200, 201]
