import os
import django
from dotenv import set_key

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from intranet.services.google_drive import get_drive_service
from core.models import Membro
from gestao_membros.models import Departamento
from midia_lgpd.models import PastaVirtual
from django.conf import settings

GDRIVE_ROOT_ID = '1ZulCvedeEykQN-Vkj0B2i3o-MLqrZsd1'
ENV_FILE = os.path.join(settings.BASE_DIR, '.env')

def create_folder(service, name, parent_id):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
    return folder.get('id')

def get_or_create_master_folder(service, name, parent_id):
    results = service.files().list(
        q=f"'{parent_id}' in parents and name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    
    items = results.get('files', [])
    if items:
        print(f"[OK] Pasta Mestra '{name}' encontrada ({items[0]['id']})")
        return items[0]['id']
    else:
        print(f"[NEW] Criando Pasta Mestra '{name}'...")
        return create_folder(service, name, parent_id)

def main():
    print("=== INICIANDO SINCRONIZACAO GDRIVE ===")
    service = get_drive_service()
    if not service:
        print("Erro: Nao foi possivel conectar ao GDrive.")
        return

    # 1. Pastas Mestras
    usuarios_id = get_or_create_master_folder(service, "Usuarios", GDRIVE_ROOT_ID)
    deptos_id = get_or_create_master_folder(service, "Departamentos", GDRIVE_ROOT_ID)

    # 2. Atualizar .env
    print("Atualizando .env...")
    set_key(ENV_FILE, 'GDRIVE_USUARIOS_FOLDER_ID', usuarios_id)
    set_key(ENV_FILE, 'GDRIVE_DEPARTAMENTOS_FOLDER_ID', deptos_id)
    
    # Atualizar settings memory for this script
    settings.GDRIVE_USUARIOS_FOLDER_ID = usuarios_id
    settings.GDRIVE_DEPARTAMENTOS_FOLDER_ID = deptos_id

    # 3. Sincronizar Membros
    print("\n--- Sincronizando Membros ---")
    membros = Membro.objects.all()
    for membro in membros:
        pasta_raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=membro).first()
        if pasta_raiz:
            if not pasta_raiz.gdrive_folder_id:
                print(f"[GDrive] Criando pasta para Membro: {membro.first_name}")
                pasta_raiz.gdrive_folder_id = create_folder(service, pasta_raiz.nome, usuarios_id)
                pasta_raiz.save(update_fields=['gdrive_folder_id'])
            
            pasta_comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados', dono_membro=membro).first()
            if pasta_comp and not pasta_comp.gdrive_folder_id:
                print(f"[GDrive] Criando pasta Compartilhados para Membro: {membro.first_name}")
                pasta_comp.gdrive_folder_id = create_folder(service, pasta_comp.nome, pasta_raiz.gdrive_folder_id)
                pasta_comp.save(update_fields=['gdrive_folder_id'])

    # 4. Sincronizar Departamentos
    print("\n--- Sincronizando Departamentos ---")
    deptos = Departamento.objects.all()
    for depto in deptos:
        pasta_raiz = PastaVirtual.objects.filter(tipo_pasta='departamento', departamento=depto).first()
        if pasta_raiz:
            if not pasta_raiz.gdrive_folder_id:
                print(f"[GDrive] Criando pasta para Departamento: {depto.nome}")
                pasta_raiz.gdrive_folder_id = create_folder(service, pasta_raiz.nome, deptos_id)
                pasta_raiz.save(update_fields=['gdrive_folder_id'])
            
            pasta_comp = PastaVirtual.objects.filter(tipo_pasta='compartilhados', departamento=depto).first()
            if pasta_comp and not pasta_comp.gdrive_folder_id:
                print(f"[GDrive] Criando pasta Compartilhados para Departamento: {depto.nome}")
                pasta_comp.gdrive_folder_id = create_folder(service, pasta_comp.nome, pasta_raiz.gdrive_folder_id)
                pasta_comp.save(update_fields=['gdrive_folder_id'])

    print("\n=== SINCRONIZACAO CONCLUIDA ===")

if __name__ == '__main__':
    main()
