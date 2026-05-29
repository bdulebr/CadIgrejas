# 7. Instrução Global (De IA para IA) - Como Recriar a Intranet PV Enseada

Este documento é um **Master Prompt**. Caso seja necessário migrar o sistema, iniciar a infraestrutura do zero ou transferir o projeto para uma nova inteligência artificial, copie e cole o bloco de texto abaixo. Ele instruirá a IA a recriar a arquitetura exata da plataforma.

---

## Copie o bloco abaixo e envie para a IA:

```text
Atue como um Arquiteto de Software Sênior, Engenheiro de Segurança e Especialista em UI/UX focado no ecosistema Python/Django.
Sua missão é desenvolver (ou reconstruir) a "Intranet PV Enseada", um sistema completo de gestão corporativa e eclesiástica, focado em alta usabilidade, segurança extrema e design imersivo.

### 1. STACK TECNOLÓGICA (Obrigatória)
- **Backend:** Python 3.10+ e Django 5.x. (Padrão MVC/MVT).
- **Frontend:** HTML5 semântico, HTMX (para requisições assíncronas estilo SPA), TailwindCSS via CDN (para estilização rápida) e Lucide Icons.
- **Banco de Dados:** SQLite3 local (projetado para máxima flexibilidade sem depender de instâncias externas).
- **Outras libs Python:** `python-decouple` (gerenciamento de variáveis de ambiente), `reportlab` (geração robusta de relatórios PDF).

### 2. FILOSOFIA DE DESIGN (UI/UX)
Você está terminantemente proibido de entregar interfaces de aparência "padrão/antiga". O sistema DEVE ter uma aparência PREMIUM e corporativa.
- **Dark Mode Nativo:** Fundo primário utilizando a cor `slate-900`. 
- **Tipografia:** Utilize "Inter" ou fontes sem serifa modernas.
- **Glassmorphism (Efeito Vidro):** Os cartões, modais e barra lateral devem usar transparência (ex: `bg-white/5` ou `bg-gray-800/80`) com desfoque de fundo (`backdrop-blur-md`).
- **Micro-interações:** Botões devem possuir `hover`, `active` states (ex: `hover:scale-105 transition-all`), e toasts (alertas) devem deslizar na tela suavemente.
- O sistema deve ser responsivo (Mobile First e Desktop App) com arquivos `manifest.json` e `sw.js` configurados para ser um PWA.

### 3. ARQUITETURA DO SISTEMA E MÓDULOS (APPS DO DJANGO)
A plataforma é segmentada em 5 aplicativos principais. Mantenha os acoplamentos o mais frouxo possível:

#### A. CORE (O Coração)
- App principal com as configurações base e templates vitais (como `base.html`).
- **Autenticação de Usuário (Membro):** Sobrescreva o `AbstractUser` do Django para incluir cargos personalizados, fotos de perfil, bloqueios e múltiplos departamentos associados.
- **Dashboard Sysadmin (God Mode):** Painel que permite gerir o `.env` dinamicamente (trocar de BASE_URL, Senha de E-mail), colocar o site em Modo Manutenção e editar os templates HTML de e-mail usando WYSIWYG (Summernote). Deve possuir um botão "Zerar Banco" (Apagando dados de histórico, MAS PRESERVANDO AS CONTAS DOS MEMBROS).
- **Zero-Trust Audit (Hash Chain):** Tabela `LogAuditoria`. Toda ação em qualquer tabela deve inserir um log aqui, assinando digitalmente (`hash_atual = SHA256(dados_acao + hash_anterior)`). A cadeia de hashes nunca deve quebrar.

#### B. GESTÃO DE MEMBROS
- CRUD completo do rebanho, com atribuições de cargos.
- **Avisos Globais:** Sistema para disparar comunicados (salvos no DB e disparados via e-mail) para todos os membros ou apenas para os alocados em um departamento específico.

#### C. ESCALAS (Complexidade Alta)
- **Editor Visual:** Interface Drag & Drop para montar as escalas mensais.
- Os modelos devem ligar: `CompetenciaEscala` -> Departamento -> `Membro` <-> `Função`.
- **Prevenção de Burnout:** Disparar aviso na tela se tentar alocar a mesma pessoa mais de 5 vezes no mesmo mês.
- **PDF Generator:** Ao publicar a escala, gerar automaticamente um PDF esteticamente premium utilizando `reportlab` e salvar na pasta `media/`.
- **Disparo Automático:** Qualquer alteração na escala de alguém deve gerar um disparo de e-mail HTML com logotipo do departamento e o botão para o painel pessoal.

#### D. MÍDIA E LGPD
- Motor para gestão de "Termos de Consentimento".
- Faça upload do PDF, gere um `token_acesso` único e inquebrável, e gere uma URL absoluta para o voluntário.
- Quando o voluntário clica via celular, ele deve ver um botão verde gigante para "Aceitar os Termos Digitalmente". Esse aceite é guardado no banco e substitui arquivos físicos.

#### E. ALMOXARIFADO
- Controle de Inventário Físico (Equipamentos) e Lotes Perecíveis (Alimentos).
- Painel para "Empréstimos de Ferramentas" e devoluções. 
- Dashboards com métricas e avisos críticos se um Lote de Alimentos for expirar em X dias.

### 4. DIRETRIZES DE ESTABILIDADE E CÓDIGO
- **Source of Truth de Links:** Nunca utilize `request.build_absolute_uri()` cegamente. Utilize uma variável de ambiente chamada `BASE_URL` no seu arquivo `.env`. Ao enviar e-mails ou gerar PDFs, construa os links absolutos baseados no `settings.BASE_URL`.
- **Emails:** Todos os envios de e-mails devem ser encapsulados em funções (ex: `enviar_email_html`) que utilizam templates locais.
- **Segurança Brute-Force:** Se um membro usar a ferramenta de "Esqueci minha senha" e errar o token/tentativas seguidas por mais de 10 vezes, congele a conta temporariamente.
- Não confie na infraestrutura padrão do Django Admin; construa todo o painel gerencial no próprio frontend da aplicação.

Comece a pensar no modelo estrutural, levante os questionamentos cruciais sobre as regras de negócio e apresente o plano de arquitetura.
```
