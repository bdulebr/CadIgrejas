# Intranet Administrativa - PV Enseada (CadIgrejas)

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite/PostgreSQL](https://img.shields.io/badge/Database-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Tailwind/CSS](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![AI Integrações](https://img.shields.io/badge/AI-Groq%20%7C%20Gemini-orange?style=for-the-badge)
![LIBRAS](https://img.shields.io/badge/🤟_LIBRAS-Surdos-0052cc?style=for-the-badge)
![Leitor de Tela](https://img.shields.io/badge/🔊_Leitor_de_Tela-Cegos-0052cc?style=for-the-badge)
![Alto Contraste](https://img.shields.io/badge/🌓_Alto_Contraste-Baixa_Visão-0052cc?style=for-the-badge)


Este repositório contém o código-fonte da **Intranet Administrativa oficial** desenvolvida para a igreja Palavra de Vida Enseada (CadIgrejas). A plataforma foi construída em Python com o framework Django (ASGI/WSGI) para servir como um ecossistema ERP completo, autônomo e de alta segurança.

---

## 🚀 Visão Geral do Sistema (O que a plataforma faz)

O projeto "CadIgrejas" vai muito além de um simples cadastro. Ele substitui 100% dos processos manuais e planilhas espalhadas, centralizando todas as bases de dados e processos humanos, financeiros, patrimoniais, pastorais e educacionais da igreja. O projeto é arquitetado sob a lei (LGPD), possui **Integrações Nativas** (WhatsApp, E-mail, Google Drive) e alavanca pesadamente a **Automação e Inteligência Artificial** para se auto-gerenciar e facilitar a vida da liderança.

A arquitetura adota uma abordagem modular severa (Micro-apps do Django). O sistema é baseado em hierarquias e *Zero-Trust*, onde um departamento não acessa os dados de outro departamento a não ser que o usuário possua "Permissão de Leitura" ou seja "Líder" daquele setor.

---

## 🧩 Detalhamento Completo dos Módulos

### 1. 🛡️ Core & SysAdmin (O Cérebro do Sistema)
O módulo mestre acessível exclusivamente pela diretoria e desenvolvedores.
- **Painel de Telemetria:** Monitoramento ao vivo do Servidor (Uso de CPU, RAM, Disco, Tamanho do DB, IP, Variáveis de Ambiente Ocultas).
- **Chave-Mestra (Master Switches):** Controle absoluto que permite travar envios globais de e-mail ou WhatsApp a qualquer momento.
- **Cão de Guarda de Invasões (Erro 403):** Vigilância ativa! Se qualquer usuário (ou visitante anônimo) tentar acessar uma rota não autorizada, o sistema aciona uma tela do "Eversinho Bravo", captura os dados do invasor (Nome, IP, Departamento) e dispara, via Thread em segundo plano, Alertas para os administradores no WhatsApp e E-mail, gravando o incidente no "Histórico de Invasões 403".
- **Gestão de Links Rápidos e Atalhos:** Controle dos atalhos fixados no topo do painel para toda a liderança.
- **Backups Automáticos DB:** Ferramenta mestre de backup que gera arquivos locais ou sobe para nuvem sob demanda.

### 2. 🧠 Motores de Inteligência Artificial e Automação (AI Daemon)
A infraestrutura está acoplada a um motor de IA Autônomo e schedulers nativos (APScheduler).
- **AI Auto-Engineer:** Um processo "Daemon" em background (`ai_daemon.py`) vigia continuamente a fila de erros internos do sistema (500 Server Error). Se detectar um bug de código provocado pelo ambiente, ele notifica a fila, invoca a IA da Google (Gemini) ou Groq, envia a *stack trace*, e gera *patches de código automáticos* para tentar manter a estabilidade do sistema sem a intervenção humana imediata.
- **Eversinho (Agente IA Autônomo com Function Calling):** Muito mais que um chatbot, o Eversinho agora é uma **IA Agente** integrada nativamente ao Google GenAI. Ele possui "poderes" reais sobre a plataforma baseados nos privilégios do usuário logado (RBAC). Ele executa ações via ferramentas (`eversinho_tools.py`) para: gerenciar Escalas, consultar e gerenciar Membros e acessar Dossiês Pastorais.
- **Universal Bug Hunter (Spider v0.2):** Um rastreador interno (backend test client) alimentado por um vasto Dicionário de Sobrevivência (Mapeamento profundo de +50 falhas críticas Python/Django/SQLite/JS). Ele varre ativamente rotas, intercepta anomalias de banco, falhas lógicas ou de timezone e gera laudos precisos com Causa e Solução em tempo real.
- **Cron Jobs Diários:**
  - **Rotinas Pós-Meia-Noite:** Todos os dias à meia-noite, a plataforma realiza backups silenciosos e varre o almoxarifado em busca de produtos vencendo na semana, fixando recados automáticos na timeline.
  - **Lembretes Manhã:** Todo dia às 08:00 dispara e-mails e Zaps de lembrete sobre Aconselhamentos Pastorais ou Cursos que acontecerão no dia seguinte.

### 3. 👤 Gestão de Membros e Visitantes
O coração dos recursos humanos da igreja.
- **Fichas Cadastrais Completas:** Gerencia endereço, contatos, foto, e histórico do membro.
- **Painel de Timeline Departamental (Mural):** Cada departamento (Música, Casais, etc) possui um mural ao estilo "Rede Social Corporativa" para publicar avisos gerais.
- **Integração Visitantes:** Portal independente para acompanhar pessoas novas que visitaram a igreja e automatizar o Follow-Up.
- **Criação de Carteirinhas / Perfis:** Geração de identificações digitais.
- **Cofre PV Drive:** Cada membro tem o seu drive virtual pessoal atrelado ao GDrive para receber cópias dos PDFs assinados (LGPD ou Termos).

### 4. 💰 Tesouraria Integrada
Software financeiro completo para controle contábil pastoral.
- **Lançamentos Simples e Recorrentes:** Fluxo de Entradas (Receitas, Dízimos, Ofertas) e Saídas (Despesas Fixas e Variáveis).
- **Gestor de Relatórios:** Geração avançada do DRE (Demonstrativo do Resultado do Exercício) e fluxo de caixa contábil.
- **Conciliação e Fechamento:** Exportação automatizada de fechamentos mensais no formato Excel (`.xlsx`), diretamente anexados e enviados via e-mail para aprovação da mesa diretora e conselho fiscal.

### 5. 💞 Ministério de Casais (Educação)
Ambiente de EaD (Ensino à Distância) e Controle Acadêmico para Cursos de Família.
- **Gestão de Cursos e Turmas:** Controle de data de início, fim, carga horária, regras de limite de faltas e aulas criadas.
- **Chamada e Frequência:** Lista de chamada eletrônica por aula e cálculo percentual de assiduidade. Reprovação automática se o limite for atingido.
- **Material Didático e Entregas:** Permite fazer upload de apostilas para alunos e recebimento de tarefas anexadas.
- **Portal de Certificação:** Se o aluno passar nos requisitos do curso, o sistema gera dinamicamente um Certificado PDF com Layout Premium e envia automaticamente ao WhatsApp e E-mail.
- **Gamificação (Trilha):** Rastreamento em qual "Fase de vida" o casal está (Namorados, Noivos, Aconselhamento, Altar, etc).

### 6. 🛋️ Atendimento e Gabinete Pastoral
Gestão e agenda de clínica pastoral.
- **Marcação e Fila:** Criação de Agendamentos (Data, Hora, Local) com o Pr. Titular ou auxiliares.
- **Lembretes Antecipados:** Notificação via Cron de que amanhã haverá o encontro, evitando faltas.
- **Dossiê Forense:** Possibilidade do Pastor guardar as anotações sensíveis da sessão e níveis de crise (acessível apenas por ele).

### 7. 📦 Almoxarifado, Patrimônio e PDV
Controle absoluto do que entra, sai e quem deve.
- **Lotes de Alimentos/Insumos:** Controle com `data de validade` para evitar desperdícios (avisos de vencimento integrados ao Mural).
- **Gestor de Empréstimos e Patrimônio (Cautela):** Qualquer equipamento caro (microfones, ferramentas, chaves) emprestado gera dinamicamente e assina eletronicamente um **Termo de Responsabilidade em PDF**. O sistema rastreia devoluções em atraso.
- **PDV (Ponto de Venda/Cantina):** Módulo ágil para venda de lanches e combos integrados à tesouraria.

### 8. 📅 Escalas Inteligentes (Voluntariado)
Ferramenta para líderes construírem a grade de trabalho.
- **Layout Kanban Drag & Drop:** Interface inovadora onde o líder de Louvor, Mídia, etc., simplesmente "arrasta" o rosto do membro da lateral para os dias (Dom Manhã, Dom Noite) e define suas funções ou ausências.
- **Geração de Escala PDF:** Um clique exporta toda a escala do mês formatada, colorida e estruturada para impressão em PDF.
- **Regras de Carga Horária:** Protege os membros contra "sobrecarga" de atividades dentro do mês.

### 9. ⚖️ Mídia & Segurança (LGPD Compliant)
Total aderência às diretrizes globais da Lei Geral de Proteção de Dados.
- **Termos e Aceites Eletrônicos:** Gerencia e emite o termo oficial de cessão de uso de imagem e de proteção de dados.
- **Assinatura Remota via Link:** O voluntário/membro não precisa logar; o sistema dispara um Link Único via SMS/WhatsApp para ele abrir no celular, ler e apertar "Aceitar".
- **Geração de 2ª Via Automática:** Todo documento aceito pelo sistema gera uma via legal em PDF criptografado e deposita sem intermediários na pasta Drive do Líder, além de enviar uma cópia anexa pro e-mail do titular com as *logs JSON* de auditoria da ação.

### 10. 🔑 Engine de Permissões e Auditoria Extrema
- **Níveis Hierárquicos Dinâmicos:** As permissões não são "chumbadas". Você vincula um Membro -> a um Departamento -> com um Cargo. O sistema faz a interseção matemática entre tudo e libera os menus adequados no frontend.
- **LogAuditoria (Logbook):** Todas as ações gravadas por líderes geram histórico. Quem excluiu? Quem alterou? Tudo fica marcado com JSON das diferenças para auditoria futura.

---

## 🛠 Como Rodar o Projeto (Produção e Local)

### Pré-Requisitos
- **Python 3.10+** e **Git**
- **Servidor:** Funciona em Windows Server, Linux (Ubuntu), ou via Docker.
- Recomendamos o uso de Servidores ASGI (Daphne, Uvicorn, Hupper) para a Intranet, devido à necessidade das Threads Assíncronas.

### Passos de Instalação Rápida
1. **Clone o Repositório**
   ```bash
   git clone https://github.com/bdulebr/CadIgrejas.git
   cd CadIgrejas
   ```
2. **Crie e Ative o Ambiente (VENV)**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   ```
3. **Instale as Bibliotecas**
   ```bash
   pip install -r requirements.txt
   ```
4. **Crie as Variáveis Ambientais**
   Faça uma cópia do arquivo `.env.example` e renomeie para `.env`. Configure suas chaves:
   - `SECRET_KEY`, `EMAIL_HOST`, `EMAIL_PASSWORD`, `GROQ_API_KEY`, etc.
5. **Rodar Migrações e Inicializar**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser  # Crie a conta do Sysadmin Supremo
   python manage.py bootstrap_sistema # Sincroniza tabelas mestre no banco
   ```
6. **Inicializar o Servidor**
   - **Dev Mode:** `python manage.py runserver`
   - **Production (Windows script):** Duplo clique no `run_prod.bat` (Inicializa o Daphne ASGI, Coleta Estáticos e aciona o Cão de Guarda da IA simultaneamente).

### Acesso Inicial
Acesse a aplicação pela rota inicial de login: `http://127.0.0.1:8000`.

---
*Arquitetado e Desenvolvido para servir ao Corpo. Em constante refinamento corporativo e autonômo.*
