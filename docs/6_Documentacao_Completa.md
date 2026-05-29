# Manual Completo do Sistema (Resumo Técnico)

## Índice
1. Visão Arquitetural
2. Setup do Ambiente
3. Árvore de Diretórios
4. Scripts e Rotinas de Manutenção
5. Como Adicionar Novos Módulos

---

## 1. Visão Arquitetural
A plataforma consolida as metodologias PWA e SPA no frontend (utilizando HTMX) servidas unicamente pelas Engines de Templates clássicas do Django no backend.
Isto reduz complexidades severas em pipelines de deploy e viabiliza a execução num VPS super simples ou até RaspberryPi na rede local da igreja.

## 2. Setup do Ambiente
Com o Python 3.10+ instalado:
```bash
python -m venv venv
venv\Scripts\activate  # (Windows)
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Crie a conta marcos@pvenseada.org
python manage.py runserver
```

## 3. Árvore de Diretórios Principais
- `/intranet/`: Configurações mestres (`settings.py`), WSGI/ASGI e roteadores primários.
- `/core/`: App mestre, autenticação global, templates base (navbars, toolbars) e dashboards globais.
- `/almoxarifado/`, `/escalas/`, `/gestao_membros/`, `/midia_lgpd/`: Os sub-aplicativos contendo regras de negócio, models e views perfeitamente isolados.
- `/media/`: Assets isolados enviados por usuários em tempo real.

## 4. Scripts e Rotinas de Manutenção
Nesta infraestrutura, o `manage.py` não é a única forma de realizar manutenções. O app `core` implementa no próprio navegador lógicas cruciais:
- **Modo Manutenção**: Suspende acesso de membros comuns, congelando inserções para realização de backups frios em segurança (DB Wipe ou Snapshot).
- **Wipe (Zerar Sistema)**: O botão perigoso do Sysadmin. Ele varre o DB limpando lixo cumulativo (escalas, PDFs, comprovantes físicos), mas preservando as contas dos membros (Acessos).

## 5. Como Adicionar Novos Módulos
Sempre siga o princípio de responsabilidade isolada!
1. Crie o novo app: `python manage.py startapp financeiro`
2. Registre-o no `intranet/settings.py`.
3. Herde os padrões visuais estendendo `{% extends 'core/base.html' %}` no Frontend.
4. Adicione suas URLs dinâmicas para o `intranet/urls.py`.
5. Se for enviar arquivos e imagens, use SEMPRE as pastas virtuais dentro de `media/` para que o Sysadmin consiga auditar.
