"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/services/google_calendar.py
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

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials', 'intranet-pv-enseada-2e7f89952449.json')

def get_calendar_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Usa o e-mail do admin para impersonar via Domain-Wide Delegation no Workspace
    if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
        creds = creds.with_subject(settings.EMAIL_HOST_USER)

    service = build('calendar', 'v3', credentials=creds)
    return service

def criar_evento_escala(escala):
    """
    Sincroniza a escala recém criada com a Agenda oficial do Google.
    """
    service = get_calendar_service()
    if not service:
        print("Aviso: Arquivo JSON de Service Account do Google não encontrado. O pulando sincronização com Agenda.")
        return None

    # Exemplo de Payload para o Google Calendar
    evento = {
        'summary': f'Escala: {escala.membro_escalado.first_name} - {escala.departamento_alocado.nome}',
        'description': f'Escala de voluntariado gerada pela Intranet PV Enseada.',
        'start': {
            'dateTime': f"{escala.data_escala}T{escala.horario_inicio}-03:00",
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': f"{escala.data_escala}T{escala.horario_fim}-03:00",
            'timeZone': 'America/Sao_Paulo',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 60},
            ],
        },
    }

    try:
        calendar_id = settings.GCALENDAR_ID if getattr(settings, 'GCALENDAR_ID', None) else 'primary'
        event = service.events().insert(calendarId=calendar_id, body=evento).execute()
        print(f"Evento criado no Google Calendar: {event.get('htmlLink')}")
        return event.get('htmlLink')
    except Exception as e:
        print(f"Erro ao integrar com o Google Calendar: {str(e)}")
        return None
