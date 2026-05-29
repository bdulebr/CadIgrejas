# Informações Críticas e Regras de Negócio

Este arquivo consolida "as pedras angulares" que mantêm a Intranet funcionando.

## 1. Liderança Fixa & Super Admins
Os acessos da Liderança Executiva nunca podem ser destruídos, nem mesmo se o botão global de "Wipe" (Zerar Banco) for acionado pelo SysAdmin. São eles:
- **`marcos@pvenseada.org`** -> SUPER ADMIN GERAL
- **`paula@pvenseada.org`** -> Gestão Central do Setor de Escalas
- **`douglas@pvenseada.org`** -> Gestão Central do Setor Almoxarifado

## 2. Segurança Contra Bloqueios
Para evitar sequestros de contas ou perda sistêmica de acesso:
- Se um membro errar a recuperação de senha **mais de 10 vezes**, o fluxo dele é travado por motivos de força bruta. O desbloqueio passa a ser exigido exclusivamente via intervenção manual pelo SysAdmin.

## 3. Centralização da "Source of Truth" (BASE_URL)
No passado, a plataforma dependia do `request.build_absolute_uri()` para fabricar links locais. Com a arquitetura Cloud-Native, o sistema adota estritamente a configuração global chamada **`BASE_URL`**.
- Se for rodar local: `http://127.0.0.1:8000`
- Se for produção: O link de nuvem (ex: `https://intranet.pvenseada.org`)
*Atenção:* Alterar o `BASE_URL` no SysAdmin reflete em frações de segundos em todos os novos PDFs gerados, e-mails disparados, e links de assinatura enviados.

## 4. Pastas Críticas e Estrutura Imutável
A pasta raiz do projeto possui estruturas vitais que o Git pode (ou não) rastrear:
- `db.sqlite3`: Coração de todos os dados do banco.
- `.env`: Arquivo blindado e ignorado que guarda senhas de SMTP, chave do Gemini e a BASE_URL. Editável via Sysadmin!
- `media/`: Todos os uploads (Pdfs, Logs, Notas fiscais, Termos assinados e Fotos de perfil). Cuidado no deploy, garanta o backup diário desta pasta!


## 🛡️ Arquitetura Zero-Trust e Blindagem
O sistema opera sob o conceito de **Zero-Trust (Confiança Zero)**, mesmo para usuários líderes e SysAdmins. Isso garante trilhas de auditoria imutáveis:
- **Servidores da Palavra (Membros):** Não podem ser excluídos do banco de dados (proteção rígida). Em vez de excluir, o perfil deve ser Inativado. Isso impede que escalas passadas e vínculos históricos sejam corrompidos.
- **Ativos Patrimoniais e Lotes de Alimentos:** Não podem ser deletados. Itens do Almoxarifado quebram ou acabam, portanto, o status deve ser alterado (Baixado/Quebrado/Saída) para manter rastreabilidade logística e financeira exata.
- **Privilégios Sysadmin:** APENAS o SysAdmin tem a chave mestra para excluir configurações estruturais (como Avisos do Mural, Funções de Setor, Slots de Escalas e Departamentos).
- **Zerar Banco de Dados:** Existe um recurso exclusivo do SysAdmin no Dashboard que permite fazer um "Soft-Wipe", apagando movimentações e escalas, mas mantendo a base estrutural (Usuários, Departamentos) intacta para viradas de ano/ciclo.
