import json
import hmac
import hashlib
import os
import mimetypes
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import ConfiguracaoSistema
from intranet.services.whatsapp_service import WhatsAppClient

@csrf_exempt
def whatsapp_webhook(request):
    """
    Endpoint para receber eventos de Webhook da Meta (WhatsApp Cloud API).
    Responde ao GET (desafio de verificação) e ao POST (mensagens recebidas).
    """
    config = ConfiguracaoSistema.objects.first()
    if not config or not config.whatsapp_ativo:
        return HttpResponseForbidden("Webhook inativo.")

    verify_token = config.whatsapp_verify_token or ""
    app_secret = config.whatsapp_app_secret or ""

    if request.method == 'GET':
        # Validação do Webhook pela Meta
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == verify_token:
                return HttpResponse(challenge)
            return HttpResponseForbidden("Token de verificação inválido.")
        return HttpResponseForbidden("Parâmetros ausentes.")

    elif request.method == 'POST':
        # 1. Obter a assinatura do header
        signature = request.headers.get("X-Hub-Signature-256", "")
        body = request.body

        # 2. Validar assinatura de segurança (HMAC SHA-256)
        if app_secret:
            expected_signature = hmac.new(
                app_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()

            if f"sha256={expected_signature}" != signature:
                return HttpResponseForbidden("Assinatura inválida. Tentativa de invasão bloqueada.")

        # 3. Parse do JSON
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        # 4. Extrair mensagens
        try:
            if "entry" in data:
                for entry in data["entry"]:
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        if "messages" in value:
                            for msg in value["messages"]:
                                telefone_origem = msg.get("from")
                                msg_type = msg.get("type")
                                texto_recebido = ""

                                if msg_type == "text":
                                    texto_recebido = msg.get("text", {}).get("body", "")
                                elif msg_type == "interactive":
                                    texto_recebido = "[Botão Clicado] " + msg.get("interactive", {}).get("button_reply", {}).get("title", "")
                                elif msg_type in ["document", "image"]:
                                    media = msg.get(msg_type, {})
                                    media_id = media.get("id")
                                    mime_type = media.get("mime_type", "")
                                    ext = mimetypes.guess_extension(mime_type) or ".bin"

                                    # Usa o serviço interno para baixar
                                    client = WhatsAppClient()
                                    from django.conf import settings
                                    save_dir = os.path.join(settings.MEDIA_ROOT, "whatsapp_recebidos")
                                    os.makedirs(save_dir, exist_ok=True)

                                    filename = f"{msg_type}_{telefone_origem}_{msg.get('id')}{ext}"
                                    save_path = os.path.join(save_dir, filename)

                                    if client.download_media(media_id, save_path):
                                        texto_recebido = f"[Anexo Recebido] Salvo em: {save_path}"
                                    else:
                                        texto_recebido = f"[Falha no download do anexo]"
                                else:
                                    texto_recebido = f"[Mensagem não suportada do tipo: {msg_type}]"

                                # Opcional: Futuramente salvar no banco de dados
                                print(f"==== WHATSAPP RECEBIDO de {telefone_origem} ====\n{texto_recebido}")

        except Exception as e:
            print(f"Erro no parser do webhook do WhatsApp: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return JsonResponse({"status": "success"})

    return HttpResponseForbidden("Método não permitido.")
