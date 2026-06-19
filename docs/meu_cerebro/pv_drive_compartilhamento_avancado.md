# Módulo: PV Drive - Compartilhamento Avançado e Segurança

## Arquitetura de Permissões (`midia_lgpd.models.PermissaoPVDrive`)
O motor de compartilhamento do PV Drive não usa as lógicas padrões de permissão de pasta do Google Drive ou do Windows; ele usa um modelo polimórfico proprietário no banco de dados.

### Conceitos Chave
- **Alvo:** Uma permissão pode ter como alvo um `Departamento` inteiro (`alvo_departamento`) ou um `Membro` específico (`alvo_membro`).
- **Item:** Uma permissão pode compartilhar uma `PastaVirtual` (`pasta`) ou um arquivo isolado `ArquivoMidia` (`arquivo`).
- **Missão Impossível (Autodestruição):** O campo `is_autodestruir` (Boolean) define se o arquivo/pasta vai se auto-destruir após o primeiro acesso com senha. A destruição ocorre setando `is_ativo = False` após o usuário obter sucesso em baixar/visualizar o arquivo.

## Camada de Segurança e Bypass
A segurança nativa das rotas de visualização e download (`visualizar_arquivo` e `baixar_arquivo`) foram reescritas com a função `check_arquivo_acesso()`.
Essa função consolida as regras de negócio:
1. Se for Super Admin, acesso liberado.
2. Se for dono do arquivo, acesso liberado.
3. Se o arquivo pertencer a um departamento no qual o usuário é líder/sublider, acesso liberado.
4. Se houver uma `PermissaoPVDrive` ativa:
   - Sem senha: Acesso liberado (e auto-destruição engatilhada se for o caso).
   - Com senha (`senha_acesso` não nulo): O sistema retorna a ID da permissão e a view força um redirecionamento HTTP para a view de cofre virtual (`acesso_protegido_senha`).
   - Se o usuário destranca o cofre com a senha correta (enviada por e-mail), a sessão recebe uma flag `request.session['acesso_liberado_ID'] = True` e ele é devolvido para a rota de download.

## Geração de Atalhos no GDrive
Mesmo com o motor de segurança local, o sistema tenta sincronizar atalhos visuais no Google Drive. Se o alvo tiver a pasta `Compartilhados`, o sistema utiliza a Google Drive API (`service.files().create(body=shortcut_metadata...)`) com o `mimeType='application/vnd.google-apps.shortcut'` para linkar o ID da pasta/arquivo original no drive do destinatário.

## UI e Frontend
- A interface `pv_drive.html` usa HTMX e Alpine.js (`x-data`) para interatividade sem reload.
- Existe uma aba exclusiva `meus_compartilhamentos.html` para os donos dos arquivos gerenciarem e revogarem permissões ativas.
- A pasta "Compartilhados" é gerada automaticamente pelo backend na raiz de cada usuário na primeira vez que ele acessa o drive, sendo flagada como `is_sistema=True` para prevenir exclusão ou renomeio acidental.
