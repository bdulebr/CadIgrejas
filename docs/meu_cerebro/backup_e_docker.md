# Evolução de Backups e Infraestrutura (Docker + Linux VPS)

**Data:** 22/06/2026
**Objetivo:** Adicionar feedback visual de nuvem nos backups, adicionar criptografia e compressão ao baixar DB, e preparar Docker e Dependências para Ubuntu LTS.

## Modificações no Backup

1. **Modelagem:**
   - Adicionado `enviado_nuvem` (Booleano) e `gdrive_file_id` em `core/models.py/DatabaseBackup`.
2. **Download Seguro (ZIP):**
   - O `sysadmin_baixar_backup` não expõe mais o `.sqlite3` cru na rota GET.
   - Requer `POST` com a senha do usuário logado (`request.POST.get('senha_admin')`).
   - Usa `pyzipper` (AES) para empacotar e enviar como `backup_db.sqlite3.zip`.
3. **Upload (GDrive):**
   - A função `sysadmin_backup_gdrive` agora salva `enviado_nuvem=True` e `gdrive_file_id=X` quando completa. O painel (HTML) inspeciona esse boolean para desenhar um ícone de nuvem ☁️ nas tabelas.

## Modificações de Infraestrutura (Ubuntu + Docker)

1. **Dependências (`requirements.txt`):**
   - Injetamos `psycopg2-binary` para conexão nativa do PostgreSQL.
   - Injetamos `pyzipper` para compactação segura de ZIP.
2. **Arquivos de Contêiner (`docker-compose.yml` e `Dockerfile`):**
   - Trocamos o gunicorn padrão pelo **Daphne**, afinal temos WebSockets rodando ativamente para o SysAdmin Spider.
   - Adicionamos o serviço do **Redis** no Compose.
   - O web-service possui link direto para `USE_REDIS=True` com `REDIS_URL=redis://redis:6379/1`.
   - Volumes e portas estão isolados, a VPS só precisa rodar `docker-compose up -d --build`.

**Conformidade:** LGPD preservada; todos logs de segurança mantidos. Cérebro atualizado conforme Regra 1.
