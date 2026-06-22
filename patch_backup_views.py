with open("core/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace sysadmin_baixar_backup
old_baixar = """@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_baixar_backup(request, backup_id=None):
    import os
    from django.conf import settings
    from core.models import DatabaseBackup

    if backup_id:
        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        db_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)
        filename = os.path.basename(backup.arquivo)
    else:
        db_path = 'db.sqlite3'
        filename = "backup_db.sqlite3"

    if not os.path.exists(db_path):
        messages.error(request, "Banco de dados não encontrado no disco.")
        return redirect('sysadmin_dashboard')

    with open(db_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/x-sqlite3')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response"""

new_baixar = """@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_baixar_backup(request, backup_id=None):
    import os
    from django.conf import settings
    from core.models import DatabaseBackup

    if request.method != 'POST':
        messages.error(request, "Ação não permitida via GET. Use o formulário com sua senha.")
        return redirect('sysadmin_dashboard')

    senha = request.POST.get('senha_admin', '')
    if not request.user.check_password(senha):
        messages.error(request, "Senha de administrador incorreta. Download cancelado por segurança.")
        return redirect('sysadmin_dashboard')

    if backup_id:
        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        db_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)
        filename = os.path.basename(backup.arquivo)
    else:
        db_path = 'db.sqlite3'
        filename = "backup_db.sqlite3"

    if not os.path.exists(db_path):
        messages.error(request, "Banco de dados não encontrado no disco.")
        return redirect('sysadmin_dashboard')

    import io
    import pyzipper

    try:
        mem_zip = io.BytesIO()
        with pyzipper.AESZipFile(mem_zip, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(senha.encode('utf-8'))
            zf.write(db_path, arcname=filename)

        mem_zip.seek(0)
        response = HttpResponse(mem_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao gerar ZIP criptografado: {str(e)}")
        return redirect('sysadmin_dashboard')"""

content = content.replace(old_baixar, new_baixar)


# Replace sysadmin_backup_gdrive
old_gdrive = """        file_id = upload_backup_to_gdrive()
        messages.success(request, f"Backup enviado com sucesso para o Google Drive! ID: {file_id}")"""

new_gdrive = """        file_id = upload_backup_to_gdrive()
        if backup_id:
            backup.enviado_nuvem = True
            backup.gdrive_file_id = file_id
            backup.save()
        messages.success(request, f"Backup enviado com sucesso para o Google Drive! ID: {file_id}")"""

content = content.replace(old_gdrive, new_gdrive)

with open("core/views.py", "w", encoding="utf-8") as f:
    f.write(content)

print("core/views.py patched.")
