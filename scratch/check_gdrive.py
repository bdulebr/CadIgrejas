import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from intranet.services.google_drive import get_drive_service

service = get_drive_service()
folder_id = '1ZulCvedeEykQN-Vkj0B2i3o-MLqrZsd1'

print(f"Buscando pastas filhas de {folder_id}...")
results = service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    spaces='drive',
    fields='nextPageToken, files(id, name, mimeType)',
    supportsAllDrives=True,
    includeItemsFromAllDrives=True
).execute()

items = results.get('files', [])

if not items:
    print('Nenhum arquivo encontrado.')
else:
    for item in items:
        print(f"{item['name']} ({item['id']}) - {item['mimeType']}")
