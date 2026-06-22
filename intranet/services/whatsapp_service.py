"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/services/whatsapp_service.py
* DESCRIÇÃO: Motor Avançado de envio de mensagens via Meta Cloud API (WhatsApp)
* INSPIRAÇÃO: Mesquita Assessoria Contábil API
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.2
* DATA DA ÚLTIMA ALTERAÇÃO: 22/06/2026
"""
import requests
from django.conf import settings

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

    def send_text(self, to: str, body: str) -> dict:
        """
        Envia uma mensagem de texto simples usando a API Oficial da Meta.
        """
        if not self._check_status(to):
            return {"error": "Servico pausado ou sem credenciais"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body
            }
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            return {"status_code": response.status_code, "response": response.json()}
        except Exception as e:
            return {"error": str(e)}

    def send_document(self, to: str, document_url: str, filename: str = "documento.pdf") -> dict:
        """
        Envia um documento (ex: Termo Cautela, Certificado Casais).
        A URL do documento precisa ser pública para a Meta baixar e enviar.
        """
        if not self._check_status(to):
            return {"error": "Servico pausado ou sem credenciais"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            return {"status_code": response.status_code, "response": response.json()}
        except Exception as e:
            return {"error": str(e)}

    def send_button_message(self, to: str, body: str, buttons: list) -> dict:
        """
        Envia uma mensagem com botões interativos (ex: Aceite LGPD).
        buttons: Lista de strings (max 3) com os nomes dos botões.
        """
        if not self._check_status(to):
            return {"error": "Servico pausado ou sem credenciais"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

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
            "to": to,
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

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            return {"status_code": response.status_code, "response": response.json()}
        except Exception as e:
            return {"error": str(e)}

    def download_media(self, media_id: str, save_path: str) -> bool:
        """
        Baixa uma mídia recebida via webhook (ex: Comprovante Tesouraria).
        """
        if not self.access_token:
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            url_req = requests.get(f"https://graph.facebook.com/{self.api_version}/{media_id}", headers=headers, timeout=10)
            if url_req.status_code != 200:
                print(f"Erro ao obter URL da midia: {url_req.json()}")
                return False

            media_url = url_req.json().get('url')
            if not media_url:
                return False

            media_resp = requests.get(media_url, headers=headers, timeout=30)
            if media_resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(media_resp.content)
                return True
            return False
        except Exception as e:
            print(f"Erro no download da midia: {e}")
            return False

# Funções Wrapper para compatibilidade com a implementação inicial (se houver)
def enviar_whatsapp_mensagem(destinatario_numero, mensagem):
    client = WhatsAppClient()
    result = client.send_text(destinatario_numero, mensagem)
    return result.get('status_code') in [200, 201]

def enviar_whatsapp_pdf(destinatario_numero, arquivo_url, filename="documento.pdf"):
    client = WhatsAppClient()
    result = client.send_document(destinatario_numero, arquivo_url, filename)
    return result.get('status_code') in [200, 201]
