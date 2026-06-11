# CÉREBRO DA IA - REGRAS GLOBAIS E DIRETRIZES DO PROJETO

ESTE DOCUMENTO É A FONTE DE VERDADE ABSOLUTA. DEVE SER CONSULTADO ANTES DE QUALQUER NOVA IMPLEMENTAÇÃO.

## 1. REGRAS DE GIT E VERSIONAMENTO (OBRIGATÓRIO)
- **REGRA DE OURO:** A cada final de edição, adição ou exclusão de código, é **OBRIGATÓRIO** subir para o Git de forma automática.
- Comandos padrão: `git add .`, `git commit -m "feat/fix: descrição"`, `git push origin main`.
- Arquivos pesados (ex: `*.apk`, maiores que 100MB) devem estar explicitamente no `.gitignore` para não quebrar o push no Github.

## 2. REGRAS DE MEMÓRIA E RELATÓRIOS (MEU CÉREBRO)
- **REGRA DE OURO:** Toda sessão de trabalho finalizada **DEVE** gerar um arquivo de log detalhado dentro de `DOCS/meu_cerebro/` com o formato de nome: `LOG_YYYY_MM_DD_HHhMM.md`.
- O relatório deve conter tudo que foi feito, decisões de design, arquivos alterados e pendências. Nunca confiar apenas no histórico do chat.

## 3. DIRETRIZES DE DESIGN, CORES E UI/UX
- **Sistema de Cores Psicológico:**
  - **Módulos de Gestão Corporativa/Tech** (Dashboard Geral, Almoxarifado, PDV): Tons de **Azul** e **Cinza** (segurança, sobriedade).
  - **Módulos de Liderança e Organização** (Escalas, Criação de Equipes): Tons de **Amarelo** (atenção, dinamismo).
  - **Módulos de Relacionamento e Cuidado** (CRM de Visitantes e Membros): Tons de **Rosa e Roxo** (acolhimento, calor humano, amor, vida).
- **Logotipos e Identidade:** **NUNCA** usar a logo estática (`logo.jpg`) hardcoded em templates de e-mail ou PDF se puder ser evitado. Sempre utilizar a logo dinâmica vinda do banco de dados (`ConfiguracaoSistema.igreja_logo`).
- **Horários:** Os e-mails e templates devem respeitar fielmente a agenda de horários informada (Domingo da Família, Santa Ceia, Segunda de Oração, Terça Pastoral, Quarta Profética, Quinta do Saber).

## 4. ARQUITETURA, SEGURANÇA E ZERO-TRUST
- **Departamentos de Sistema (Is_System):** Departamentos vitais como `Almoxarifado`, `CRM / Integração`, `Sysadmin`, e `Escalas` possuem proteção Zero-Trust. Eles **NUNCA** podem ser deletados via painel ou banco.
- **Motor de Auto-Healing (`bootstrap_sistema.py`):** Ao iniciar o servidor, o sistema faz verificações de integridade de pastas, banco de dados e sincronia com o GitHub. Alterações críticas devem prever que o Auto-Healing não destrua dados locais ou apague o módulo `urls.py`.
- **Pre-commit Hooks:** Existem ganchos de validação ativos (Flake8, Whitespace). Qualquer código gerado deve ser limpo e não conter espaços em branco sobrando nas quebras de linha para evitar falha no commit.

## 5. REGRAS DE ROTAS E DJANGO
- Toda nova "App" (Módulo) criada via `startapp` deve ser obrigatoriamente:
  1. Adicionada em `intranet/settings.py` (`INSTALLED_APPS`).
  2. Roteada em `intranet/urls.py`.
  3. Ter seu link registrado condicionalmente em `core/templates/core/base.html` (Sidebar).
  4. Testada utilizando o motor E2E `run_spider.py`.
