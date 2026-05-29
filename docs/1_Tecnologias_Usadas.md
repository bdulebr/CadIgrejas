# Tecnologias Usadas

## Visão Geral
A Intranet PV Enseada é um sistema moderno construído sob uma pilha ágil e performática, focada em segurança, estabilidade e experiência do usuário (UX).

## Backend
- **Python 3.10+**: Linguagem base do sistema, escolhida por sua legibilidade e ecossistema maduro.
- **Django 5.x**: Framework web principal. Utilizado pela sua arquitetura MVT (Model-View-Template), ORM poderoso, painel de admin embutido e gestão avançada de segurança (proteção CSRF, XSS, Clickjacking).
- **ReportLab**: Biblioteca Python especializada na geração programática de arquivos PDF (usado na geração das Escalas e Termos LGPD).
- **Python-Decouple / Os.Environ**: Para o gerenciamento seguro de variáveis de ambiente (`.env`).
- **Google Generative AI (Gemini)**: Integração com a API do Gemini para Inteligência Artificial (ex: análise de sentimentos e insights do BI).

## Frontend
- **HTML5 & CSS3**: Estrutura semântica nativa.
- **TailwindCSS (via CDN)**: Framework CSS utilitário para estilização rápida, responsiva e criação do Design System consistente (Glassmorphism, Dark Mode nativo).
- **HTMX**: Para requisições assíncronas (AJAX) direto no HTML, trazendo fluidez de SPA (Single Page Application) sem a complexidade de frameworks JavaScript pesados.
- **Vanilla JavaScript**: Para lógicas de interface (modais, tooltips, formatadores de formulário e service workers).
- **Lucide Icons**: Biblioteca de ícones vetoriais modernos e minimalistas.
- **Summernote**: Editor Rich Text (WYSIWYG) utilizado pelo SysAdmin para criar templates de e-mail e termos de LGPD com formatação HTML nativa.

## Infraestrutura & Armazenamento
- **SQLite3**: Banco de dados relacional embarcado e ultraleve, otimizado para o projeto atual sem necessidade de instanciar servidores externos.
- **PWA (Progressive Web App)**: Service Worker nativo `sw.js` e `manifest.json`, permitindo instalação como aplicativo nativo no celular e cache inteligente (Network-First).
- **SMTP**: Servidor de disparo de e-mails transacionais assíncronos configurado para o domínio da igreja.
