import os
import datetime
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials', 'intranet-pv-enseada-2e7f89952449.json')

def upload_backup_to_gdrive(file_path='db.sqlite3'):
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Arquivo de credenciais do Google Drive não encontrado: {SERVICE_ACCOUNT_FILE}")
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Banco de dados não encontrado: {file_path}")

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
    # Usa o e-mail do admin para impersonar via Domain-Wide Delegation no Workspace
    if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
        creds = creds.with_subject(settings.EMAIL_HOST_USER)

    service = build('drive', 'v3', credentials=creds)

    data_atual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"backup_pve_intranet_{data_atual}.sqlite3"

    file_metadata = {'name': nome_arquivo}
    if settings.GDRIVE_FOLDER_ID:
        file_metadata['parents'] = [settings.GDRIVE_FOLDER_ID]
    media = MediaFileUpload(file_path, mimetype='application/x-sqlite3')

    # Faz o upload para a raiz do drive da Service Account (ou pasta compartilhada se tiver ID)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()

    return file.get('id')
