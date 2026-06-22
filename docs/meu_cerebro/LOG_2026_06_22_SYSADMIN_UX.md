# Registro de Memória (Cérebro do Agente)
## Data: 22 de Junho de 2026 - 14h55
## Assunto: Auditoria e Correção UX/UI SysAdmin

### Contexto
O usuário reportou que a interface do painel SysAdmin estava "engolindo espaço" e que o menu de Gestão de Backups e Nuvem aparecia replicado no rodapé de todas as abas. Além disso, foi solicitado um "Goal" para auditar o funcionamento de todos os botões e recursos deste módulo de controle mestre.

### Ações Executadas (Frontend)
1. **O Bug das Abas**: O bloco de "Gestão de Backups" `<div class="bg-gray-900/50 ...` estava posicionado fora de qualquer diretiva `x-show` do Alpine.js, tornando-se órfão e quebrando o layout principal.
2. **Correção**: Criei uma nova aba exclusiva chamada `Banco de Dados & Backups` (ID `backup`) na barra superior e empacotei o bloco inteiro para dentro dela: `<div x-show="activeTab === 'backup'" style="display: none;" x-transition>`.
3. **Menu Superior Flex**: O botão "Teste E2E (Spider)" também estava fora da tag `<div class="flex">`, o que o empurrava para baixo. Ele foi realocado para dentro do container de navegação.

### Ações Executadas (Backend)
Foi verificado todo o arquivo `core/views.py` para atestar a segurança e o funcionamento dos endpoints chamados pelos botões:
- `sysadmin_desbloquear_ip`: Chama corretamente a lib `axes` (reset por IP ou geral).
- `sysadmin_limpar_cache`: Utiliza a API de cache oficial do Django `cache.clear()`.
- `sysadmin_zerar_banco`: Avaliado. Ele bloqueia o apagamento da conta master `marcos@pvenseada.org` de forma explícita. Funcional.
- `sysadmin_toggle_manutencao`, `toggle_email`, `toggle_whatsapp`: Todos atuam isoladamente revertendo o estado booleano de `ConfiguracaoSistema`.

O Painel agora tem um design fluido e todas as abas funcionam como vitrines modulares.
