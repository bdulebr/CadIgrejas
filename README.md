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

Este repositório contém o código-fonte da **Intranet Administrativa oficial** desenvolvida para a igreja Palavra de Vida Enseada (CadIgrejas). A plataforma foi construída de ponta a ponta em Python com o framework Django (ASGI/WSGI) para servir como um ecossistema ERP completo, autônomo, seguro e altamente acessível.

---

## 🚀 Visão Geral do Sistema

O projeto "CadIgrejas" vai muito além de um simples sistema de cadastro. Ele foi arquitetado para substituir **100% dos processos manuais e planilhas descentralizadas**, unificando todas as bases de dados e fluxos de trabalho humanos, financeiros, patrimoniais, pastorais e educacionais da igreja.

Desenvolvido com foco total em usabilidade (UI/UX Premium) e **Compliance Legal (LGPD)**, o sistema alavanca Integrações Nativas (WhatsApp, E-mail, Google Drive) e **Automação de Inteligência Artificial** para se auto-gerenciar e facilitar o dia a dia da liderança.

A arquitetura adota uma abordagem modular robusta, separada por "Micro-apps" do Django. Todo o sistema é baseado no conceito de *Zero-Trust*, onde um departamento não tem acesso aos dados de outro, a menos que o usuário possua "Permissão de Leitura" ou seja designado como "Líder" daquele setor.

---

## 🌟 Diferenciais Tecnológicos

### 🤖 Inteligência Artificial Nativa (Eversinho)
O sistema conta com o "Eversinho", uma IA integrada que atua tanto como um assistente para o usuário final quanto como um **Cão de Guarda de Segurança**. Se ocorrerem erros severos de código (500) ou se houver uma tentativa de invasão em rotas não autorizadas (403), a IA imediatamente captura a anomalia, registra logs de auditoria e dispara mensagens de alerta no WhatsApp e no E-mail da diretoria técnica.

### ♿ Acessibilidade Universal (Para Todos!)
O CadIgrejas foi pensado para não deixar ninguém para trás. Implementamos um módulo universal de acessibilidade que injeta em todas as páginas do sistema:
- **Tradução em LIBRAS:** Avatar 3D oficial do Governo Federal (VLibras) que traduz todo o site para a Língua Brasileira de Sinais, com suporte a dicionário interativo.
- **Leitor de Tela Nativo (Text-to-Speech):** Utilizando a *Web Speech API* do navegador, pessoas cegas ou com dificuldades de leitura podem ouvir o conteúdo de qualquer página do sistema com um simples clique, sem depender de softwares ou extensões externas.
- **Alto Contraste Extremo:** Otimização severa de cores (fundo super escuro com fontes de altíssima luminosidade) para pessoas com baixa visão, operando por cima de todo o layout original.
- **Controle de Zoom Dinâmico (A+ / A-):** Aumento escalonado das fontes, salvando a preferência do usuário de forma persistente.

### 📱 Progressive Web App (PWA) e Responsividade
Construído com *TailwindCSS* de ponta a ponta, o sistema é 100% Mobile-First. Além disso, conta com integração via *Service Workers* e manifestos web (PWA), permitindo que qualquer líder instale a Intranet no celular como se fosse um aplicativo nativo (iOS e Android), trabalhando com caching inteligente para conexões lentas.

---

## 🧩 Detalhamento Completo dos Módulos

O ecossistema está dividido em 10 grandes pilares que funcionam de forma integrada e autônoma:

### 1. 🛡️ Core & SysAdmin (O Cérebro do Sistema)
O módulo mestre acessível exclusivamente pela diretoria e desenvolvedores principais.
- **Painel de Telemetria:** Monitoramento ao vivo da saúde do servidor, incluindo uso de CPU, RAM, Disco, Tamanho do DB, IP do cliente e ambiente.
- **Chaves-Mestras (Master Switches):** Controle absoluto que permite travar envios globais de e-mail ou WhatsApp a qualquer momento.
- **Log de Invasões:** Histórico gravado de cada tentativa de acesso não autorizado, capturando dados do invasor (Nome, IP, Departamento) com disparo via Thread em segundo plano para administradores.
- **Gestão Global de UI:** Controle dos links rápidos e atalhos fixados no topo do painel para toda a liderança da igreja.
- **Gerador de Backups:** Ferramenta mestre que gera dumps completos do Banco de Dados SQLite em formato ZIP/RAR, garantindo que nenhum byte de dado seja perdido.

### 2. 📁 Mídia, LGPD & PV Drive (Compliance e Nuvem Privada)
- **Termos de Aceite LGPD e Direitos Autorais:** O sistema de governança dispara automaticamente e-mails criptografados com termos dinâmicos. Quando o usuário clica, ele assina digitalmente através do sistema (salvando IP, Timestamp e User Agent).
- **Trilhas de Auditoria Legais:** Todas as assinaturas geram um documento final em PDF ("Segunda Via") que é guardado de maneira definitiva no servidor e enviado para o e-mail do titular.
- **PV Drive (Nuvem Interna):** Um "Google Drive" próprio construído do zero, permitindo criação infinita de subpastas, upload de arquivos ilimitados, pré-visualização inline de PDFs/Imagens e um sistema de **Compartilhamento Interno** complexo, onde você pode ceder acesso de um arquivo a membros ou a departamentos inteiros.

### 3. 📦 Almoxarifado & Patrimônio
Esqueça a prancheta. Todo o inventário da igreja na palma da mão.
- **Gestão de Categorias e Itens:** Registro detalhado de bens (Som, Câmeras, Instrumentos, Limpeza).
- **Geração de QR Codes:** O sistema plota PDFs prontos para impressão em impressoras térmicas contendo QR Codes individuais para cada item. Ao colar no equipamento e bipar a câmera do celular, o sistema abre a ficha técnica do item instantaneamente.
- **Logs de Movimentação:** Histórico absoluto de quem pegou, quando pegou e quando devolveu um item patrimonial.
- **Fallback Automático de Impressão:** Se o PDF falhar ao ser renderizado em HTML/CSS complexo, um backend de redundância gera uma versão simplificada garantindo que o Almoxarife nunca fique na mão.

### 4. 👥 Gestão de Membros & Liderança
- **Fichas Cadastrais Complexas:** Perfis ricos contendo dados pessoais, habilidades ministeriais, data de consagração, histórico disciplinar e fotos em base64/arquivos de mídia armazenados via CDN ou localmente.
- **Gráficos Dinâmicos e Aniversariantes:** O Dashboard exibe relatórios visuais sobre o crescimento da congregação e os aniversariantes do mês.
- **Hierarquias Rigorosas:** O controle não é feito apenas por "É admin ou não?". Existe uma malha de permissões granulares de Leitura e Edição, permitindo que sub-líderes gerenciem apenas suas próprias ovelhas sem enxergar as finanças ou outras áreas críticas.

### 5. 📅 Escalas (Worship / Voluntariado / Recepção)
- **Criação Rápida de Equipes:** Líderes arrastam e soltam membros em posições pré-definidas (Ex: Teclado, Bateria, Diácono da Porta Principal).
- **Alertas Automáticos Inteligentes:** Quando a escala é finalizada, um gatilho envia um E-mail estilizado e um aviso no WhatsApp da pessoa avisando a data e o horário.
- **Exportação Flexível:** Geração de PDFs em alta resolução e visualização modo "Tabela" para imprimir e colar no mural.

### 6. 👋 Visitantes & Consolidação
- **Totem de Autoatendimento:** Uma tela pública focada em altíssima usabilidade (design clean, botões grandes) para ficar aberta num Tablet no hall da igreja, onde o visitante coloca seus dados rapidamente.
- **Pipeline de Acompanhamento (CRM):** O visitante entra na esteira de consolidação, passando pelas etapas (Primeiro Contato, Ligação Pastoral, Inserção em Pequeno Grupo, Membresia). O líder de integração controla tudo visualmente.

### 7. 🛒 PDV (Ponto de Venda / Cantina e Eventos)
Um módulo assustadoramente rápido focado em alta vazão para balcão.
- **Frente de Caixa em Tela Cheia:** Interface estilo "Caixa de Supermercado" projetada para ser usada em monitores Touch ou teclados (Atalhos rápidos para Finalizar Compra).
- **Fechamento Cego e Relatórios Noturnos:** O operador de caixa faz seu fechamento, e o sistema emite relatórios diários automáticos detalhando sangrias, pagamentos em PIX vs Dinheiro vs Cartão.
- **Impressão de Cupom:** Formatação otimizada nativamente em larguras `80mm` e `58mm` para integrar instantaneamente com impressoras térmicas (Daruma, Bematech, Elgin), com corte de papel e aviso de recibo não-fiscal.

### 8. 💰 Tesouraria & Financeiro
- **Dashboard de Saúde Financeira:** Controle rígido de Entradas (Dízimos, Ofertas, Doações Específicas) e Saídas (Pagamento de Luz, Som, Projetos Sociais).
- **Centros de Custos e Categorização:** Cada centavo é rastreado para o departamento exato de onde saiu ou entrou.
- **Auditoria de Caixa:** Relatórios gerenciais e balancetes exportados diretamente para PDF via WeasyPrint para enviar às autoridades contábeis da Sede.

### 9. 🎓 Ministério de Casais (E-Learning e Cursos)
Uma verdadeira faculdade corporativa e financeira acoplada no sistema.
- **Área do Aluno Criptografada:** Portal do aluno onde ele visualiza as ementas, o material de aula e o controle de frequências.
- **Geração de Certificados Customizados:** Ao concluir o curso, o Django plota um certificado lindíssimo em alta resolução e marca d'água com o nome do aluno, carga horária e validade, disponível para baixar na hora.
- **Motor Financeiro Interno:** Diferente da Tesouraria principal, este módulo controla os recebimentos das *inscrições do curso*. Emissão de cobranças, e-mails de "Não se esqueça da sua parcela" e avisos amigáveis para os estudantes.

### 10. 🛋️ Atendimento Pastoral (Aconselhamento)
O módulo mais blindado do sistema.
- **Sigilo Absoluto:** As anotações das sessões pastorais são gravadas e criptografadas em alto nível, não podendo ser vistas por nenhum outro departamento a não ser o corpo de Pastores.
- **Ficha de Acompanhamento Clínico-Espiritual:** Registro da queixa inicial, histórico de encontros anteriores, e agendamento de retorno, compilando a "vida pastoral" do membro em uma tela única.

---

## 🛠️ Stack Tecnológico e Ferramentas

O CadIgrejas foi construído sobre uma arquitetura Full-Stack moderna focada em performance bruta e escalabilidade a longo prazo:

- **Backend & Core:** Python 3.12+ acoplado com o ecossistema super-seguro do **Django 5.x**.
- **Banco de Dados:** Embora o desenvolvimento inicial ocorra em ambiente **Windows**, o sistema final roda de forma nativa e isolada em servidores **Linux**. Em produção, o SQLite dá lugar à versão mais recente do **PostgreSQL**, garantindo durabilidade e paralelismo sob alta carga.
- **Cache e Background Jobs:** Integração profunda com **Redis** para gerenciamento de cache de altíssima velocidade, sessões seguras e processamento de filas em segundo plano (como envio de e-mails e inteligência artificial).
- **Frontend Engine:** HTML5 purista com **Tailwind CSS v3** em modo JIT, *Glassmorphism* e Dark Modes nativos. Interatividade fluida e assíncrona gerenciada por **HTMX** e **Alpine.js**, eliminando o peso de uma SPA tradicional.
- **Processamento de PDFs:** `WeasyPrint` integrado nativamente para relatórios complexos, etiquetas de QRCode e certificados.

---

## 💻 Instalação e Deploy (Ambiente de Produção Linux)

O sistema foi arquitetado para subir de forma autônoma e orquestrada. Para provisionar o sistema em um servidor Linux (VPS Ubuntu/Debian), o local correto de instalação é clonar o projeto e orquestrar tudo via Docker na raiz do projeto. Siga os passos:

1. **Clone o repositório e acesse a raiz:**
   ```bash
   git clone https://github.com/bdulebr/CadIgrejas.git
   cd CadIgrejas
   ```

2. **Configure as Variáveis de Ambiente de Produção:**
   Copie o arquivo base e insira suas credenciais definitivas (Senhas do PostgreSQL, chaves da IA, token de E-mail/WhatsApp).
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Suba o Ecossistema Docker:**
   O arquivo de orquestração irá baixar, compilar e amarrar os contêineres do Django (via Gunicorn), Nginx Reversos, PostgreSQL e Redis automaticamente.
   ```bash
   docker-compose up -d --build
   ```

4. **Migrações e Configuração Inicial:**
   Por fim, crie as tabelas no PostgreSQL e colete os arquivos estáticos:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py collectstatic --noinput
   docker-compose exec web python manage.py createsuperuser
   ```

Tudo pronto! O Nginx já está interceptando o tráfego e seu ERP de igreja está operando a todo vapor em ambiente corporativo.

---

> *"O choro pode durar uma noite, mas a alegria vem pela manhã." (Salmos 30:5)*
> **Sistema construído para o Reino, com excelência.**
