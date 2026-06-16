"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/services/google_drive.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials', 'intranet-pv-enseada-2e7f89952449.json')

def get_drive_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Usa o e-mail do admin para impersonar via Domain-Wide Delegation no Workspace
    # Se der erro de unauthorized_client, é porque o Workspace não autorizou essa delegação.
    # if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
    #     creds = creds.with_subject(settings.EMAIL_HOST_USER)
    service = build('drive', 'v3', credentials=creds)
    return service

def upload_arquivo_drive(file_path, titulo):
    """
    Sincroniza um arquivo de mídia enviado para o servidor local com o Google Drive,
    servindo como backup na nuvem.
    """
    service = get_drive_service()
    if not service:
        print("Aviso: Sem credenciais do Google Drive. Upload para nuvem ignorado.")
        return None

    try:
        file_metadata = {'name': titulo}
        if not settings.GDRIVE_FOLDER_ID:
            print("Erro: 'GDRIVE_FOLDER_ID' não está configurado. O Google Workspace exige o ID de uma pasta em um 'Drive Compartilhado'.")
            return None

        file_metadata['parents'] = [settings.GDRIVE_FOLDER_ID]

        # Em produção, detectar mimeType adequadamente
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()

        print(f"Arquivo sincronizado no Google Drive com sucesso: {file.get('webViewLink')}")
        return file.get('webViewLink')

    except Exception as e:
        print(f"Erro no backup para o Google Drive: {str(e)}")
        return None
