# Intranet Administrativa - PV Enseada (CadIgrejas)

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Tailwind/CSS](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

Este repositório contém o código-fonte da Intranet Administrativa oficial desenvolvida para a igreja Palavra de Vida Enseada (CadIgrejas). A plataforma foi construída em Python com o framework Django para servir como um ecossistema completo e centralizado de gestão para múltiplos departamentos da instituição.

---

## 🚀 Visão Geral do Sistema

O projeto "CadIgrejas" não é apenas um sistema de cadastro de membros, mas um verdadeiro ERP departamental. Ele substitui processos manuais em papel, centraliza bases de dados e gerencia com maestria recursos humanos, financeiros e patrimoniais da igreja, protegendo os dados sob a lei (LGPD) e alavancando Automação e Inteligência Artificial.

A arquitetura adota uma abordagem modular (Micro-apps do Django), o que significa que cada departamento da igreja roda em seu próprio módulo, com permissões estritas baseadas em níveis hierárquicos e responsabilidades ("Pastores", "Líderes", "Membros", etc.).

---

## 🧩 Módulos Principais

### 👤 Gestão de Membros e Perfis
O coração do sistema. Gerencia o cadastro completo dos membros, visitantes e frequentadores.
- Acompanhamento de níveis hierárquicos.
- Atribuição de Lideranças de Departamentos.
- Geração de perfis digitais.

### 💰 Tesouraria Integrada
Módulo dedicado à gestão financeira da igreja local.
- Lançamento de Receitas, Despesas e Dízimos/Ofertas.
- Conciliação Bancária.
- Relatórios avançados de DRE e fluxo de caixa.
- Exportação automatizada de fechamento mensal em planilhas Excel (.xlsx) enviadas diretamente por e-mail para a sede.

### 💞 Ministério de Casais
Um ambiente acadêmico para o acompanhamento dos cursos de noivos e casados.
- Criação e Gestão de Turmas e Cursos.
- Matrículas de casais e acompanhamento de frequência.
- Emissão automatizada de Certificados em PDF que são salvos e enviados por e-mail aos formandos.

### 📦 Almoxarifado e Patrimônio
Módulo de controle do inventário físico e fluxo de empréstimos.
- Cadastro e rastreio do patrimônio da igreja.
- Controle rigoroso de movimentações de estoque.
- Geração dinâmica e automatizada de **Termos de Cautela e Responsabilidade** em PDF. O sistema captura as informações, assina o documento via sistema e o envia ao e-mail do retirante sob diretrizes de responsabilidade civil.

### 📅 Gestão de Escalas
Organização centralizada do trabalho voluntário.
- Criação de escalas de serviço e avisos de lembretes automáticos para voluntários baseando-se nas datas escaladas.

### ⚖️ Mídia & Segurança LGPD
O guardião jurídico do sistema.
- Controle, geração e assinatura digital de Termos de Consentimento de Uso de Imagem.
- Possui fluxos automatizados que comunicam o titular via links públicos para o aceite e arquiva as assinaturas em nuvem.
- Integração facilitada com solicitações que podem ser engatilhadas com e-mail ou envio direto para WhatsApp.

### ⚙️ Painel Sysadmin e Motor de Permissões
Painel mestre acessível exclusivamente por super-administradores do sistema.
- Painel vivo de Telemetria do Servidor (CPU, RAM, Disco, Saúde do Banco de Dados).
- Chave-Mestra (*Master Switch*) do fluxo global de E-mails do sistema (podendo travar/parar envios globais num clique).
- Engine robusto de permissões verificadas `ManyToMany` onde módulos se auto-regulam validando a qual departamento o líder tem acesso, evitando vazamento ou corrupção de dados entre diferentes equipes.

### 🧠 Inteligência Artificial (AI Daemon e Auto-Engineer)
A infraestrutura está acoplada com um cérebro inteligente nativo.
- Geração de *insights* espirituais ou textos motivacionais diretamente na dashboard do usuário (Alimentado por Groq LLM).
- **Auto-Engineer:** A arquitetura possui rotinas que, em caso de erro interno grave, tentam realizar auto-correções, consultam memórias ou alertam o desenvolvedor por e-mail sobre *stack traces* e anomalias irrecuperáveis do sistema em background.

---

## 🛠 Como Rodar o Projeto Localmente

### Pré-Requisitos
- Python 3.10+
- Git

### 1. Clonar o Repositório
```bash
git clone https://github.com/bdulebr/CadIgrejas.git
cd CadIgrejas
```

### 2. Preparar Ambiente Virtual
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente (.env)
Crie um arquivo chamado `.env` na pasta raiz e popule-o com suas chaves locais e de banco de dados (confira os campos requeridos nas dependências de email e de IA se for ativá-la).
```env
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app

GROQ_API_KEY=sua_api_key_groq_aqui
```

### 5. Configurar Banco de Dados e Rodar
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Crie seu usuário sysadmin
python manage.py runserver
```
Acesse a aplicação no seu navegador: `http://127.0.0.1:8000`.

---
*Projeto desenvolvido de forma corporativa para uso interno sob arquitetura de microsserviços do Django.*
