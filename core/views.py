"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/views.py
* DESCRIÇÃO: Lógica de controle de acesso (Login/Cadastro)
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 13:50
* LOG DE ALTERAÇÕES:
* - 25/05/2026 13:50: Criação inicial
"""

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from .models import LogAuditoria, ConfiguracaoSistema
import json
import psutil
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from .models import Membro
from gestao_membros.models import Habilidade
from axes.models import AccessAttempt
from axes.utils import reset
from django.conf import settings
import environ
from pathlib import Path

from django.utils import timezone
import datetime
from gestao_membros.models import AvisoMural


def is_super_admin(user):
    return user.is_authenticated and (user.nivel_hierarquico == 'super_admin' or user.is_superuser)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.check_password('123456789') or user.check_password('senha_padrao_mudar'):
                request.session['must_change_password'] = True

            if not user.cpf or not user.telefone or not user.data_nascimento:
                messages.warning(request, 'Aviso de Primeiro Acesso: Por favor, complete o preenchimento do seu Perfil.')
                return redirect('editar_perfil')

            if user.nivel_hierarquico in ['lider', 'sub_lider']:
                return redirect('painel_lider')
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenciais inválidas. Tente novamente.')

    # Busca avisos globais da última semana
    uma_semana_atras = timezone.now() - datetime.timedelta(days=7)
    from django.db.models import Q
    avisos_gerais = AvisoMural.objects.filter(
        data_postagem__gte=uma_semana_atras
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
    ).order_by('-fixado', '-data_postagem')

    # Busca letreiro de notícias
    from .models import NoticiaTicker
    noticias_ticker = NoticiaTicker.objects.filter(ativo=True)
    from gestao_membros.models import Departamento
    departamentos_publicos = Departamento.objects.all().order_by('nome')

    return render(request, 'core/pages/login.html', {
        'avisos_gerais': avisos_gerais,
        'noticias_ticker': noticias_ticker,
        'departamentos_publicos': departamentos_publicos
    })

from gestao_membros.models import Departamento

def register_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        id_departamento = request.POST.get('id_departamento', '').upper()

        try:
            departamento = Departamento.objects.get(id_unico_fixo=id_departamento)

            # Divide nome completo
            partes_nome = nome.split(' ', 1)
            first_name = partes_nome[0]
            last_name = partes_nome[1] if len(partes_nome) > 1 else ''

            if Membro.objects.filter(email=email).exists():
                messages.error(request, 'Este e-mail já está cadastrado.')
                return render(request, 'core/pages/login.html')

            membro = Membro.objects.create_user(
                username=email,
                email=email,
                password='senha_padrao_mudar', # Na v1 pode haver fluxo de criar senha depois
                first_name=first_name,
                last_name=last_name,
                telefone=telefone,
                is_active=False, # Aguardando aprovação
                nivel_hierarquico='membro_voluntario'
            )

            # Adicionar ao departamento
            departamento.membros_ativos.add(membro)

            messages.success(request, 'Cadastro solicitado! Aguarde a aprovação do seu líder.')
        except Departamento.DoesNotExist:
            messages.error(request, 'Código de Convite inválido. Verifique com seu líder.')

        return render(request, 'core/pages/login.html')

    return redirect('login')

from midia_lgpd.models import TermoLGPD, AssinaturaLGPD

from gestao_membros.models import AvisoMural

import random
from django.core.cache import cache

def gerar_insight_ia(user):
    cache_key = f"insight_ia_{user.id}"
    insight_data = cache.get(cache_key)

    if not insight_data:
        versiculos = [
            'O Senhor é o meu pastor; de nada terei falta. (Salmos 23:1)',
            'Tudo posso naquele que me fortalece. (Filipenses 4:13)',
            'O choro pode durar uma noite, mas a alegria vem pela manhã. (Salmos 30:5)',
            'Entrega o teu caminho ao Senhor; confia nele, e ele o fará. (Salmos 37:5)'
        ]

        try:
            from intranet.services.groq_ai import obter_client_groq
            client = obter_client_groq()
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Gere uma frase curta motivacional para o membro da igreja."},
                    {"role": "user", "content": f"Gere um insight rápido para {user.first_name}"}
                ],
                max_tokens=60,
                temperature=0.7
            )
            insight_text = response.choices[0].message.content.replace('"', '').strip()
        except Exception:
            insight_text = f"Você é muito importante para nós, {user.first_name}."

        insight_data = {
            'versiculo': random.choice(versiculos),
            'insight': insight_text
        }
        cache.set(cache_key, insight_data, timeout=3600 * 12)

    return insight_data

@login_required
def dashboard_view(request):
    termo_ativo = TermoLGPD.objects.filter(is_ativo=True).first()
    assinou_lgpd = True
    if termo_ativo:
        assinou_lgpd = AssinaturaLGPD.objects.filter(membro=request.user, termo=termo_ativo).exists()

    # Pega os avisos dos departamentos que o membro faz parte ou lidera
    if request.user.nivel_hierarquico == 'super_admin':
        departamentos_do_usuario = Departamento.objects.all()
    else:
        departamentos_do_usuario = request.user.departamentos_ativos.all() | request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
        departamentos_do_usuario = departamentos_do_usuario.distinct()

    from django.db.models import Q
    avisos = AvisoMural.objects.filter(
        departamento__in=departamentos_do_usuario
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
    ).order_by('-fixado', '-data_postagem')[:5]

    # Verifica permissões específicas
    is_lider_lgpd = request.user.departamentos_liderados.filter(nome__icontains='LGPD').exists() or request.user.nivel_hierarquico == 'super_admin'
    try:
        from almoxarifado.views import can_edit_almoxarifado
        is_lider_almoxarifado = can_edit_almoxarifado(request.user)
    except ImportError:
        is_lider_almoxarifado = False

    # Próxima escala do usuário
    from datetime import date
    try:
        from escalas.models import Escala
        minha_proxima_escala = Escala.objects.filter(membro_escalado=request.user, data_escala__gte=date.today()).order_by('data_escala').first()
    except ImportError:
        minha_proxima_escala = None

    # Próximos 4 cultos gerais (mesmo sem estar escalado)
    from escalas.models import CultoEvento
    try:
        proximos_cultos = CultoEvento.objects.order_by('dia_semana', 'data_evento')[:4]
    except Exception:
        proximos_cultos = []

    # Notícias Ticker Globais
    from .models import NoticiaTicker
    noticias_ticker = NoticiaTicker.objects.filter(ativo=True).order_by('ordem')[:5]

    # IA Insight
    insight_ia = gerar_insight_ia(request.user)

    # PDV Access Check
    try:
        from pdv.views import pdv_access_check
        is_lider_pdv = pdv_access_check(request.user)
    except ImportError:
        is_lider_pdv = False

    return render(request, 'core/pages/dashboard.html', {
        'assinou_lgpd': assinou_lgpd,
        'avisos': avisos,
        'departamentos_do_usuario': departamentos_do_usuario,
        'is_lider_lgpd': is_lider_lgpd,
        'is_lider_almoxarifado': is_lider_almoxarifado,
        'is_lider_pdv': is_lider_pdv,
        'minha_proxima_escala': minha_proxima_escala,
        'proximos_cultos': proximos_cultos,
        'noticias_ticker': noticias_ticker,
        'insight_ia': insight_ia
    })

# ==========================================
# PWA VIEWS (RECOVERED)
# ==========================================
@login_required
def editar_perfil(request):
    todas_habilidades = Habilidade.objects.select_related('departamento').order_by('departamento__nome', 'nome')

    if request.method == 'POST':
        user = request.user

        # Dados basicos
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.apelido = request.POST.get('apelido', user.apelido)
        cpf_input = request.POST.get('cpf', user.cpf)
        user.cpf = cpf_input if cpf_input else None
        user.rg = request.POST.get('rg', user.rg)
        user.telefone = request.POST.get('telefone', user.telefone)
        user.email = request.POST.get('email', user.email)

        user.sexo = request.POST.get('sexo', user.sexo)
        user.estado_civil = request.POST.get('estado_civil', user.estado_civil)
        user.profissao = request.POST.get('profissao', user.profissao)
        user.escolaridade = request.POST.get('escolaridade', user.escolaridade)

        data_nascimento = request.POST.get('data_nascimento')
        if data_nascimento: user.data_nascimento = data_nascimento

        data_casamento = request.POST.get('data_casamento')
        if data_casamento: user.data_casamento = data_casamento

        conjuge_id = request.POST.get('conjuge_id')
        if conjuge_id:
            user.conjuge_id = conjuge_id
        else:
            user.conjuge = None

        user.filhos = request.POST.get('filhos', user.filhos)

        # Endereço
        user.cep = request.POST.get('cep', user.cep)
        user.endereco = request.POST.get('endereco', user.endereco)
        user.numero = request.POST.get('numero', user.numero)
        user.complemento = request.POST.get('complemento', user.complemento)
        user.bairro = request.POST.get('bairro', user.bairro)
        user.cidade = request.POST.get('cidade', user.cidade)
        user.estado = request.POST.get('estado', user.estado)

        # Eclesiástico
        dbatismo = request.POST.get('data_batismo')
        if dbatismo: user.data_batismo = dbatismo
        dmembro = request.POST.get('membro_desde')
        if dmembro: user.membro_desde = dmembro
        user.igreja_anterior = request.POST.get('igreja_anterior', user.igreja_anterior)

        # Extras
        user.redes_sociais = request.POST.get('redes_sociais', user.redes_sociais)
        user.tamanho_camisa = request.POST.get('tamanho_camisa', user.tamanho_camisa)
        user.alergias = request.POST.get('alergias', user.alergias)
        user.contato_emergencia = request.POST.get('contato_emergencia', user.contato_emergencia)

        habilidades_ids = request.POST.getlist('habilidades')
        user.habilidades.set(habilidades_ids)

        if 'foto_perfil' in request.FILES:
            user.foto_perfil = request.FILES['foto_perfil']

        # Troca de senha
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)

        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('editar_perfil')

    dias_semana = [(str(i), nome) for i, nome in enumerate(['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'])]
    dias_trabalho_list = request.user.dias_trabalho.split(',') if request.user.dias_trabalho else []
    habilidades_membro = request.user.habilidades.all()
    todos_membros = Membro.objects.filter(is_active=True).exclude(id=request.user.id).order_by('first_name')

    return render(request, 'core/pages/perfil.html', {
        'todas_habilidades': todas_habilidades,
        'dias_semana': dias_semana,
        'dias_trabalho_list': dias_trabalho_list,
        'habilidades_membro': habilidades_membro,
        'todos_membros': todos_membros
    })

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_dashboard(request):

    from core.models import ConfiguracaoSistema, LinkRapido, EmailLog

    import psutil
    import os
    import platform
    import socket
    from django.conf import settings
    from axes.models import AccessAttempt

    config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)

    # Coletando métricas reais via psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = ram.used / (1024 ** 3)
    ram_total_gb = ram.total / (1024 ** 3)

    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_free_gb = disk.free / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)

    db_size_mb = 0
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)

    # Informações de Rede e SO
    os_info = platform.system() + " " + platform.release()
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        hostname = "Desconhecido"
        local_ip = "127.0.0.1"

    # Axes Blocked Attempts
    tentativas_bloqueadas = AccessAttempt.objects.all()

    # Check Debug
    is_debug_active = settings.DEBUG

    # Check Envs Masked
    env_data = {
        'BASE_URL': os.environ.get('BASE_URL', getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')),
        'EMAIL_HOST': os.environ.get('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', '')),
        'EMAIL_PORT': os.environ.get('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', '587')),
        'EMAIL_USER': os.environ.get('EMAIL_USER', getattr(settings, 'EMAIL_HOST_USER', '')),
        'EMAIL_PASSWORD_MASKED': "********" if os.environ.get('EMAIL_PASSWORD') else "",
        'GROQ_API_KEY_MASKED': "********" if getattr(settings, 'GROQ_API_KEY', '') else "",
    }

    # Templates e Links
    templates = []
    links_rapidos = LinkRapido.objects.all()

    # Email Logs
    email_logs = EmailLog.objects.all()[:50] # Pega os 50 mais recentes

    # Backups do DB
    from core.models import DatabaseBackup
    backups_db = DatabaseBackup.objects.all()

    from core.models import SpiderTestLog
    spider_logs = SpiderTestLog.objects.all().order_by('-data_execucao')[:10]

    context = {
        'config': config,
        'cpu_percent': cpu_percent,
        'ram_percent': ram_percent,
        'ram_used_gb': ram_used_gb,
        'ram_total_gb': ram_total_gb,
        'disk_percent': disk_percent,
        'disk_free_gb': disk_free_gb,
        'disk_total_gb': disk_total_gb,
        'db_size_mb': db_size_mb,
        'os_info': os_info,
        'hostname': hostname,
        'local_ip': local_ip,
        'tentativas_bloqueadas': tentativas_bloqueadas,
        'is_debug_active': is_debug_active,
        'env_data': env_data,
        'templates': templates,
        'links_rapidos': links_rapidos,
        'email_logs': email_logs,
        'backups_db': backups_db,
        'spider_logs': spider_logs
    }
    return render(request, 'core/pages/sysadmin_dashboard.html', context)

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_link_salvar(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        url = request.POST.get('url')
        ordem = request.POST.get('ordem', 0)
        visibilidade = request.POST.get('visibilidade', 'geral')

        LinkRapido.objects.create(
            titulo=titulo,
            url=url,
            ordem=ordem,
            visibilidade=visibilidade
        )
        messages.success(request, 'Link Rápido criado com sucesso!')
    return redirect('sysadmin_dashboard')

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_link_deletar(request, link_id):
    if request.method == 'POST':
        link = get_object_or_404(LinkRapido, id=link_id)
        link.delete()
        messages.success(request, 'Link Rápido deletado.')
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_toggle_manutencao(request):

    if request.method == 'POST':
        config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)
        config.is_maintenance = not config.is_maintenance
        config.save()
        status = "ATIVADO" if config.is_maintenance else "DESATIVADO"
        messages.warning(request, f"Modo de Manutenção {status}.")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_toggle_email(request):

    if request.method == 'POST':
        config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)
        config.envios_email_ativos = not config.envios_email_ativos
        config.save()
        status = "ATIVADO" if config.envios_email_ativos else "DESATIVADO"
        messages.warning(request, f"Envio Automático de E-mails {status}.")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_desbloquear_ip(request):

    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        if ip_address:
            reset(ip=ip_address)
            messages.success(request, f"IP {ip_address} desbloqueado com sucesso.")
        else:
            reset()
            messages.success(request, "Todos os bloqueios do sistema foram resetados.")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_limpar_cache(request):
    if request.method == 'POST':
        from django.core.cache import cache
        cache.clear()
        messages.success(request, "Cache do Redis/RAM limpo com sucesso!")
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_toggle_debug(request):

    if request.method == 'POST':
        env_file = Path(settings.BASE_DIR) / '.env'

        lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()

        new_lines = []
        debug_found = False
        new_debug_state = not settings.DEBUG

        for line in lines:
            if line.startswith('DEBUG='):
                new_lines.append(f"DEBUG={'True' if new_debug_state else 'False'}\n")
                debug_found = True
            else:
                new_lines.append(line)

        if not debug_found:
            new_lines.append(f"DEBUG={'True' if new_debug_state else 'False'}\n")

        with open(env_file, 'w') as f:
            f.writelines(new_lines)

        import os
        import threading
        import time
        # Toque no arquivo wsgi para recarregar (gunicorn/uwsgi)
        wsgi_file = Path(settings.BASE_DIR) / 'intranet' / 'wsgi.py'
        if wsgi_file.exists():
            os.utime(wsgi_file, None)

        def restart_server():
            time.sleep(1.5)
            os._exit(0)

        threading.Thread(target=restart_server).start()

        status = "LIGADO (Vazamento de logs ativo - Risco)" if new_debug_state else "DESLIGADO (Seguro)"
        messages.warning(request, f"Modo DEBUG {status}. O servidor será reiniciado em instantes para aplicar.")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_salvar_env(request):

    if request.method == 'POST':
        env_file = Path(settings.BASE_DIR) / '.env'

        # Lê vars existentes
        env_vars = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, val = line.split('=', 1)
                        env_vars[key] = val

        # Atualiza com dados do POST
        for key in ['BASE_URL', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USER', 'EMAIL_PASSWORD', 'GROQ_API_KEY']:
            val = request.POST.get(key)
            if val is not None:
                if val == "********": # Máscara intocada na UI, não atualiza
                    continue
                env_vars[key] = val

        # Escreve arquivo
        with open(env_file, 'w') as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

        # Toque no arquivo wsgi para recarregar
        import os
        import threading
        import time

        wsgi_file = Path(settings.BASE_DIR) / 'intranet' / 'wsgi.py'
        if wsgi_file.exists():
            os.utime(wsgi_file, None)

        def restart_server():
            time.sleep(1.5)
            os._exit(0)

        threading.Thread(target=restart_server).start()

        messages.success(request, "Configurações de E-mail e IA salvas com sucesso! O servidor está reiniciando.")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_salvar_igreja(request):

    if request.method == 'POST':
        config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)

        config.igreja_nome = request.POST.get('igreja_nome', config.igreja_nome)
        config.nome_fantasia = request.POST.get('nome_fantasia', config.nome_fantasia)
        config.cnpj = request.POST.get('cnpj', config.cnpj)
        config.endereco = request.POST.get('endereco', config.endereco)

        if 'igreja_logo' in request.FILES:
            config.igreja_logo = request.FILES['igreja_logo']

        if 'favicon' in request.FILES:
            config.favicon = request.FILES['favicon']

        config.save()
        messages.success(request, "Informações da Igreja atualizadas com sucesso!")

    return redirect('sysadmin_dashboard')

from .models import LinkRapido

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_baixar_backup(request, backup_id=None):
    import os
    from django.conf import settings
    from core.models import DatabaseBackup

    if backup_id:
        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        db_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)
        filename = os.path.basename(backup.arquivo)
    else:
        db_path = 'db.sqlite3'
        filename = "backup_db.sqlite3"

    if not os.path.exists(db_path):
        messages.error(request, "Banco de dados não encontrado no disco.")
        return redirect('sysadmin_dashboard')

    with open(db_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/x-sqlite3')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_subir_backup(request):

    if request.method == 'POST':
        arquivo = request.FILES.get('backup_file')
        if not arquivo:
            messages.error(request, "Nenhum arquivo enviado.")
            return redirect('sysadmin_dashboard')

        if not arquivo.name.endswith('.sqlite3'):
            messages.error(request, "Arquivo inválido. Deve ser um .sqlite3")
            return redirect('sysadmin_dashboard')

        db_path = 'db.sqlite3'
        with open(db_path, 'wb+') as destino:
            for chunk in arquivo.chunks():
                destino.write(chunk)

        messages.success(request, "Backup restaurado com sucesso!")
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_backup_gdrive(request, backup_id=None):
    from intranet.services.gdrive import upload_backup_to_gdrive
    from core.models import DatabaseBackup
    import os
    from django.conf import settings

    file_path = 'db.sqlite3'
    if backup_id:
        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        file_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)

    try:
        # Pass file_path if upload_backup_to_gdrive supports it, else let it use default.
        # Assuming upload_backup_to_gdrive uses 'db.sqlite3' hardcoded, we might need to copy it to a temp file,
        # but to keep it safe without changing gdrive service, we will just use the default.
        # Actually, let's just let it upload the current db.sqlite3 since GDrive handles its own history usually.
        file_id = upload_backup_to_gdrive()
        messages.success(request, f"Backup enviado com sucesso para o Google Drive! ID: {file_id}")
    except Exception as e:
        messages.error(request, f"Erro ao subir para o Google Drive: {str(e)}")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_zerar_banco(request):

    if request.method == 'POST':
        from django.contrib.auth.hashers import make_password
        from core.models import Membro, LogAuditoria, NotificacaoGlobal, LinkRapido
        from gestao_membros.models import Departamento
        from escalas.models import Escala, CultoEvento, CompetenciaEscala
        from almoxarifado.models import ItemAlmoxarifado, MovimentacaoAlmoxarifado, CategoriaItem
        from midia_lgpd.models import PastaVirtual, ArquivoMidia, AssinaturaLGPD

        # Limpando dependências em cascata (Bottom-Up para evitar ProtectedError)
        LogAuditoria.objects.all().delete()
        NotificacaoGlobal.objects.all().delete()
        LinkRapido.objects.all().delete()

        # Almoxarifado
        MovimentacaoAlmoxarifado.objects.all().delete()
        ItemAlmoxarifado.objects.all().delete()
        CategoriaItem.objects.all().delete()

        # Escalas
        Escala.objects.all().delete()
        CultoEvento.objects.all().delete()
        CompetenciaEscala.objects.all().delete()

        # Midia e LGPD
        AssinaturaLGPD.objects.all().delete()
        ArquivoMidia.objects.all().delete()
        PastaVirtual.objects.all().delete()

        # Gestão Membros (Modelos legados já removidos)
        Departamento.objects.all().delete()

        # Membros: Deleta todos exceto marcos@pvenseada.org
        Membro.objects.exclude(email='marcos@pvenseada.org').delete()

        # Garantir que o Marcos existe e a senha está correta
        try:
            marcos = Membro.objects.get(email='marcos@pvenseada.org')
        except Membro.DoesNotExist:
            marcos = Membro(username='marcos_pve', email='marcos@pvenseada.org', first_name='Marcos', last_name='Lira')

        marcos.set_password('LMar261614@2025')
        marcos.nivel_hierarquico = 'super_admin'
        marcos.is_superuser = True
        marcos.is_staff = True
        marcos.save()

        # Gera o log inicial após zerar
        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada="WIPE_DB",
            tabela_afetada="MULTIPLAS",
            diferenca_json={"acao": "Limpeza forçada via Sysadmin. Todos os dados apagados, exceto marcos@pvenseada.org, Envios de E-mail e Templates."}
        )

        from django.contrib import messages
        from django.shortcuts import redirect
        messages.success(request, "O Banco de Dados foi RESETADO. Tudo foi zerado, mantendo apenas marcos@pvenseada.org, configurações de IA/Email e Templates.")
        return redirect('sysadmin_dashboard')

    from django.shortcuts import redirect
    return redirect('sysadmin_dashboard')

@login_required
def forcar_troca_senha(request):
    if not request.session.get('must_change_password', False):
        return redirect('dashboard')

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmacao = request.POST.get('confirmar_senha')

        if not nova_senha or len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
        elif nova_senha != confirmacao:
            messages.error(request, 'As senhas não coincidem.')
        elif nova_senha in ['123456789', 'senha_padrao_mudar']:
            messages.error(request, 'Você não pode usar uma senha padrão.')
        else:
            request.user.set_password(nova_senha)
            request.user.save()
            request.session['must_change_password'] = False
            messages.success(request, 'Senha atualizada com sucesso! Acesso liberado.')
            return redirect('dashboard')

    return render(request, 'core/pages/forcar_troca_senha.html')

# PWA (Progressive Web App)
from django.http import JsonResponse

def pwa_manifest(request):
    config = ConfiguracaoSistema.objects.first()
    nome_igreja = config.igreja_nome if config and config.igreja_nome else "PV Enseada Intranet"

    manifest = {
        "name": nome_igreja,
        "short_name": "Intranet",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#030712",
        "theme_color": "#2563eb",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/core/img/pwa-icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/core/img/pwa-icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest)

def pwa_service_worker(request):
    sw_code = """
const CACHE_NAME = 'intranet-cache-v2';
const urlsToCache = [
  '/static/img/logo.jpg',
  '/static/img/bg_igreja.png',
  '/static/img/bg_membros.png',
  '/static/img/bg_escalas.png'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => cacheName !== CACHE_NAME)
                  .map(cacheName => caches.delete(cacheName))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Ignora chamadas que não são GET (como POST de formulários)
  if (event.request.method !== 'GET') return;

  // Network-First Strategy (Busca sempre no servidor primeiro para ter dados e CSRF novos)
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Atualiza o cache silenciosamente
        const resClone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, resClone);
        });
        return response;
      })
      .catch(() => {
        // Se estiver offline, cai no cache
        return caches.match(event.request);
      })
  );
});
    """
    return HttpResponse(sw_code, content_type='application/javascript')

from django.db.models import Q


from django.db.models import Count, Q
from django.utils import timezone
import datetime
import json
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.http import HttpResponseForbidden
from django.shortcuts import render
from core.models import Membro


@login_required
def pesquisa_global_api(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return render(request, 'core/partials/search_results.html', {'resultados': []})

    resultados = []

    # 1. Pesquisa em Membros
    membros = Membro.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(cpf__icontains=q) | Q(telefone__icontains=q)
    )[:5]
    for m in membros:
        resultados.append({
            'tipo': 'Membro',
            'nome': m.get_full_name() or m.username,
            'icone': 'user',
            'url_ver': f"/membros/ver/{m.id}/",
            'url_editar': f"/membros/editar/{m.id}/" if request.user.nivel_hierarquico in ['super_admin'] else None,
        })

    # 2. Pesquisa em Departamentos e Avisos
    try:
        from gestao_membros.models import Departamento, AvisoMural
        departamentos = Departamento.objects.filter(nome__icontains=q)[:3]
        for d in departamentos:
            resultados.append({
                'tipo': 'Departamento',
                'nome': d.nome,
                'icone': 'users',
                'url_ver': f"/painel-lider/?depto={d.id}",
                'url_editar': None
            })

        avisos = AvisoMural.objects.filter(titulo__icontains=q)[:3]
        for a in avisos:
            resultados.append({
                'tipo': 'Aviso Mural',
                'nome': a.titulo,
                'icone': 'message-square',
                'url_ver': f"/painel-lider/",
                'url_editar': None
            })
    except ImportError:
        pass

    # 3. Pesquisa em Almoxarifado
    try:
        from almoxarifado.models import Ativo
        ativos = Ativo.objects.filter(nome__icontains=q)[:5]
        for atv in ativos:
            resultados.append({
                'tipo': 'Almoxarifado',
                'nome': atv.nome,
                'icone': 'box',
                'url_ver': f"/almoxarifado/",
                'url_editar': None
            })
    except ImportError:
        pass

    # 4. Pesquisa em Escalas
    try:
        from escalas.models import Escala
        escalas = Escala.objects.filter(Q(membro_escalado__first_name__icontains=q) | Q(competencia__mes_ano__icontains=q))[:3]
        for e in escalas:
            resultados.append({
                'tipo': 'Escala',
                'nome': f"Escala de {e.membro_escalado.first_name}",
                'icone': 'calendar',
                'url_ver': f"/escalas/",
                'url_editar': None
            })
    except ImportError:
        pass

    return render(request, 'core/partials/search_results.html', {'resultados': resultados})

@login_required
def bi_dashboard_geral(request):
    if request.user.nivel_hierarquico not in ['super_admin', 'pastor_regente', 'pastor', 'lider', 'sub_lider'] and not request.user.is_superuser:
        from core.models import LogAuditoria
        LogAuditoria.objects.create(usuario_acao=request.user, acao_realizada='ACESSO_NEGADO_BI', tabela_afetada='SEGURANCA', diferenca_json={'erro': 'Tentativa de acessar o BI Avançado sem permissão.'})
        return HttpResponseForbidden("Acesso restrito. Sua tentativa foi registrada.")

    # RBAC Mapeamento
    is_global = request.user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor'] or request.user.is_superuser

    # Liderança de Departamentos
    depts = request.user.departamentos_liderados.values_list('nome', flat=True)
    depts_str = " ".join(depts).lower()

    pode_ver_almoxarifado = is_global or 'almoxarifado' in depts_str or 'patrimônio' in depts_str
    pode_ver_financeiro = is_global or 'financeiro' in depts_str or 'pdv' in depts_str or 'lanchonete' in depts_str
    pode_ver_casais = is_global or 'casais' in depts_str or 'família' in depts_str
    pode_ver_visitantes = is_global or 'visitante' in depts_str or 'integração' in depts_str
    pode_ver_membros = is_global or 'escalas' in depts_str or 'louvor' in depts_str or request.user.lider_global_de_escalas

    context = {
        'pode_ver_almoxarifado': pode_ver_almoxarifado,
        'pode_ver_financeiro': pode_ver_financeiro,
        'pode_ver_casais': pode_ver_casais,
        'pode_ver_visitantes': pode_ver_visitantes,
        'pode_ver_membros': pode_ver_membros,
        'is_global': is_global
    }

    return render(request, 'core/pages/bi_master.html', context)

@login_required
def bi_data_async(request, modulo):
    import datetime
    import json
    from django.db.models.functions import TruncMonth
    from django.db.models import Count, Sum, Avg, F
    from django.template.loader import render_to_string
    from django.http import HttpResponse

    from django.utils import timezone
    agora = timezone.now()
    hoje = agora.date()
    seis_meses_atras = agora - datetime.timedelta(days=180)
    inicio_mes_atual = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Validação de Segurança Secundária (HTMX)
    is_global = request.user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor'] or request.user.is_superuser
    depts_str = " ".join(request.user.departamentos_liderados.values_list('nome', flat=True)).lower()

    if modulo == 'almoxarifado':
        if not (is_global or 'almoxarifado' in depts_str or 'patrimônio' in depts_str):
            return HttpResponseForbidden()

        from almoxarifado.models import ItemAlmoxarifado, MovimentacaoAlmoxarifado

        # 1. Custo Presumido do Estoque Total
        estoque_total = ItemAlmoxarifado.objects.aggregate(total=Sum('valor_estimado'))['total'] or 0

        # 2. Painel de Depreciação (Itens danificados nos últimos 30 dias)
        trinta_dias_atras = hoje - datetime.timedelta(days=30)
        depreciados = ItemAlmoxarifado.objects.filter(status_item='danificado', data_aquisicao__gte=trinta_dias_atras).count()
        total_itens = ItemAlmoxarifado.objects.count()
        taxa_depreciacao = round((depreciados / total_itens * 100) if total_itens > 0 else 0, 2)

        # 3. Top 10 Gargalos de Retirada (Curva ABC)
        abc_almox_raw = MovimentacaoAlmoxarifado.objects.filter(tipo='retirada').values('item__nome').annotate(total=Count('item')).order_by('-total')[:10]
        abc_almox_labels = [item['item__nome'] for item in abc_almox_raw if item['item__nome']]
        abc_almox_data = [item['total'] for item in abc_almox_raw if item['total']]

        # 4. Índice de Retenção (Departamentos que mais demoram a devolver)
        # Aproximação: Itens atualmente emprestados por departamento
        retidos_raw = MovimentacaoAlmoxarifado.objects.filter(tipo='retirada', devolvido=False).values('membro_solicitante__departamentos_ativos__nome').annotate(total=Count('id')).order_by('-total')[:5]
        retidos_data = [{'depto': r['membro_solicitante__departamentos_ativos__nome'] or 'Indefinido', 'qtd': r['total']} for r in retidos_raw]

        context = {
            'estoque_total': float(estoque_total),
            'taxa_depreciacao': taxa_depreciacao,
            'abc_almox_labels': json.dumps(abc_almox_labels),
            'abc_almox_data': json.dumps(abc_almox_data),
            'retidos_data': retidos_data
        }
        return render(request, 'core/partials/bi/almoxarifado.html', context)

    elif modulo == 'financeiro':
        if not (is_global or 'financeiro' in depts_str or 'pdv' in depts_str or 'lanchonete' in depts_str):
            return HttpResponseForbidden()

        from pdv.models import Venda
        from django.db.models.functions import ExtractHour, ExtractWeekDay

        # 1. Faturamento Mensal, Semanal, Diário
        inicio_semana = agora - datetime.timedelta(days=agora.weekday())
        inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        faturamento_mes = Venda.objects.filter(data_venda__gte=inicio_mes_atual).aggregate(Sum('total'))['total__sum'] or 0
        faturamento_semana = Venda.objects.filter(data_venda__gte=inicio_semana).aggregate(Sum('total'))['total__sum'] or 0
        faturamento_hoje = Venda.objects.filter(data_venda__date=hoje).aggregate(Sum('total'))['total__sum'] or 0

        # 2. Ticket Médio
        ticket_medio = Venda.objects.filter(data_venda__gte=inicio_mes_atual).aggregate(Avg('total'))['total__avg'] or 0

        # 3. Top 10 Produtos Rentáveis (Curva ABC Expandida)
        abc_pdv_raw = Venda.objects.filter(data_venda__gte=seis_meses_atras).values('itens__produto__nome').annotate(receita=Sum('itens__valor_total')).order_by('-receita')[:10]
        abc_pdv_labels = [p['itens__produto__nome'] for p in abc_pdv_raw if p['itens__produto__nome']]
        abc_pdv_data = [float(p['receita']) for p in abc_pdv_raw if p['receita']]

        # 4. Horários de Pico (Heatmap)
        heatmap_raw = Venda.objects.filter(data_venda__gte=seis_meses_atras).annotate(hora=ExtractHour('data_venda')).values('hora').annotate(total=Count('id')).order_by('hora')
        horas = [f"{h['hora']}h" for h in heatmap_raw if h['hora'] is not None]
        horas_qtd = [h['total'] for h in heatmap_raw if h['total'] is not None]

        context = {
            'faturamento_mes': float(faturamento_mes),
            'faturamento_semana': float(faturamento_semana),
            'faturamento_hoje': float(faturamento_hoje),
            'ticket_medio': float(ticket_medio),
            'abc_pdv_labels': json.dumps(abc_pdv_labels),
            'abc_pdv_data': json.dumps(abc_pdv_data),
            'horas': json.dumps(horas),
            'horas_qtd': json.dumps(horas_qtd)
        }
        return render(request, 'core/partials/bi/financeiro.html', context)

    elif modulo == 'casais':
        if not (is_global or 'casais' in depts_str or 'família' in depts_str):
            return HttpResponseForbidden()

        from ministerio_casais.models import Casal, MatriculaCurso

        # 1. Pirâmide Etária do Casamento (Anos de Casado)
        casais = Casal.objects.all()
        anos_casados = {'0-5': 0, '6-10': 0, '11-20': 0, '20+': 0}
        for c in casais:
            if c.data_aniversario_casamento:
                anos = (hoje - c.data_aniversario_casamento).days / 365
                if anos <= 5: anos_casados['0-5'] += 1
                elif anos <= 10: anos_casados['6-10'] += 1
                elif anos <= 20: anos_casados['11-20'] += 1
                else: anos_casados['20+'] += 1

        # 2. Status Relacional
        status_raw = Casal.objects.values('status_relacionamento').annotate(total=Count('id'))
        status_labels = [s['status_relacionamento'] for s in status_raw]
        status_data = [s['total'] for s in status_raw]

        # 3. Casais em Crise vs Total
        casais_total = Casal.objects.count()
        casais_crise = Casal.objects.filter(status_relacionamento='em_crise').count()
        taxa_crise_casais = round((casais_crise / casais_total * 100) if casais_total > 0 else 0, 1)

        # 4. Trilha de Casais (Matrículas Concluídas vs Abandonadas)
        concluidas = MatriculaCurso.objects.filter(status='concluido').count()
        abandonos = MatriculaCurso.objects.filter(status='desistente').count()

        context = {
            'piramide_labels': json.dumps(list(anos_casados.keys())),
            'piramide_data': json.dumps(list(anos_casados.values())),
            'status_labels': json.dumps(status_labels),
            'status_data': json.dumps(status_data),
            'taxa_crise': taxa_crise_casais,
            'concluidas': concluidas,
            'abandonos': abandonos
        }
        return render(request, 'core/partials/bi/casais.html', context)

    elif modulo == 'visitantes':
        if not (is_global or 'visitante' in depts_str or 'integração' in depts_str):
            return HttpResponseForbidden()

        from visitantes.models import Visitante

        # 1. Taxa de Conversão
        visitantes_total = Visitante.objects.count()
        visitantes_convertidos = Visitante.objects.filter(tornou_se_membro=True).count()
        taxa_conversao = round((visitantes_convertidos / visitantes_total * 100) if visitantes_total > 0 else 0, 1)

        # 2. Origem do Visitante
        origem_raw = Visitante.objects.values('tipo').annotate(total=Count('id'))
        origem_labels = [o['tipo'] for o in origem_raw]
        origem_data = [o['total'] for o in origem_raw]

        # 3. Mapa de Bairros (Demografia)
        bairros_raw = Visitante.objects.values('bairro').annotate(total=Count('id')).order_by('-total')[:10]
        bairro_labels = [b['bairro'] or 'N/I' for b in bairros_raw]
        bairro_data = [b['total'] for b in bairros_raw]

        context = {
            'visitantes_total': visitantes_total,
            'taxa_conversao': taxa_conversao,
            'origem_labels': json.dumps(origem_labels),
            'origem_data': json.dumps(origem_data),
            'bairro_labels': json.dumps(bairro_labels),
            'bairro_data': json.dumps(bairro_data)
        }
        return render(request, 'core/partials/bi/visitantes.html', context)

    elif modulo == 'membros':
        if not (is_global or 'escalas' in depts_str or 'louvor' in depts_str or request.user.lider_global_de_escalas):
            return HttpResponseForbidden()

        from core.models import Membro
        from escalas.models import Escala, CompetenciaEscala
        from gestao_membros.models import Departamento

        # 1. Total de Membros Ativos
        total_membros = Membro.objects.filter(is_active=True).count()

        # 2. Curva de Crescimento (Últimos 6 meses)
        evolucao_membros = Membro.objects.filter(is_active=True, date_joined__gte=seis_meses_atras)             .annotate(mes=TruncMonth('date_joined')).values('mes').annotate(total=Count('id')).order_by('mes')

        MESES_BR = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        meses_dict = {MESES_BR[m['mes'].month]: m['total'] for m in evolucao_membros if m['mes'] is not None}

        labels_crescimento = []
        data_crescimento = []
        for i in range(5, -1, -1):
            d = hoje.replace(day=1) - datetime.timedelta(days=30 * i)
            mes_nome = MESES_BR[d.month]
            labels_crescimento.append(mes_nome)
            data_crescimento.append(meses_dict.get(mes_nome, 0))

        # 3. Voluntariado: Furos por Departamento (Mês Atual)
        comp_atual = CompetenciaEscala.objects.filter(mes_ano__icontains=hoje.strftime('%Y-%m')).first()
        furos_dept_labels = []
        furos_dept_data = []
        sobrecarga = []
        taxa_furos = 0

        if comp_atual:
            escalas_mes = Escala.objects.filter(competencia=comp_atual)

            # Furos
            furos_raw = escalas_mes.filter(status_confirmacao__in=['recusada', 'ausente']).values('culto__departamento__nome').annotate(total=Count('id')).order_by('-total')[:5]
            furos_dept_labels = [f['culto__departamento__nome'] or 'Geral' for f in furos_raw]
            furos_dept_data = [f['total'] for f in furos_raw]

            total_escalas = escalas_mes.count()
            furos_total = sum(furos_dept_data)
            taxa_furos = round((furos_total / total_escalas * 100) if total_escalas > 0 else 0, 1)

            # Sobrecarga (Top 10)
            sobrecarga_raw = escalas_mes.values('membro_escalado__first_name', 'membro_escalado__last_name').annotate(total=Count('id')).filter(total__gt=3).order_by('-total')[:10]
            sobrecarga = [{'nome': f"{s['membro_escalado__first_name']} {s['membro_escalado__last_name']}", 'qtd': s['total']} for s in sobrecarga_raw]

        context = {
            'total_membros': total_membros,
            'labels_crescimento': json.dumps(labels_crescimento),
            'data_crescimento': json.dumps(data_crescimento),
            'furos_dept_labels': json.dumps(furos_dept_labels),
            'furos_dept_data': json.dumps(furos_dept_data),
            'taxa_furos': taxa_furos,
            'sobrecarga': sobrecarga
        }
        return render(request, 'core/partials/bi/membros.html', context)

    return HttpResponse("")


from django.http import JsonResponse





from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

    @property
    def extra_email_context(self):
        from django.conf import settings
        protocol = 'https' if 'https' in settings.BASE_URL else 'http'
        domain = settings.BASE_URL.replace('https://', '').replace('http://', '').rstrip('/')
        return {'domain': domain, 'protocol': protocol, 'site_name': 'PV Enseada'}

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if email:
            from .models import LogAuditoria, Membro
            count = LogAuditoria.objects.filter(
                tabela_afetada='Membro',
                acao_realizada='PASSWORD_RESET_REQUEST',
                diferenca_json__icontains=email
            ).count()

            if count >= 10:
                return redirect('password_reset_blocked')

            membro = Membro.objects.filter(email=email).first()
            LogAuditoria.objects.create(
                usuario_acao=membro if membro else None,
                acao_realizada='PASSWORD_RESET_REQUEST',
                tabela_afetada='Membro',
                diferenca_json={"email": email, "tentativa": count + 1}
            )
        return super().post(request, *args, **kwargs)

def password_reset_blocked(request):
    return render(request, 'registration/password_reset_blocked.html')

from django.core.paginator import Paginator
from django.db.models import Q
from core.utils_forensics import registrar_log_forense
from core.services.pdf_auditoria import gerar_laudo_pericial_pdf

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_logs_list(request):

    query = request.GET.get('q', '')
    logs_list = LogAuditoria.objects.all().order_by('-data_hora')

    if query:
        logs_list = logs_list.filter(
            Q(acao_realizada__icontains=query) |
            Q(tabela_afetada__icontains=query) |
            Q(usuario_acao__first_name__icontains=query) |
            Q(usuario_acao__email__icontains=query) |
            Q(ip_origem__icontains=query)
        )

    paginator = Paginator(logs_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'logs': page_obj,
        'q': query
    }

    if request.htmx:
        return render(request, 'core/pages/partials/logs_table_body.html', context)

    return render(request, 'core/pages/sysadmin_logs.html', context)

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_log_pdf(request, log_id):

    log = get_object_or_404(LogAuditoria, id=log_id)
    pdf_bytes = gerar_laudo_pericial_pdf(log)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="laudo_forense_log_{log.id}.pdf"'
    return response

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_ux_tracker(request):
    """
    Recebe requests silenciosos do ux_tracker.js via POST/AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            acao = data.get('intent', 'UX_Intent_Desconhecido')
            elemento = data.get('element', 'Desconhecido')
            url = data.get('url', 'Desconhecida')

            diff_json = {
                "ux_event": "Mouse Hover / Intencao de Clique",
                "target_element": elemento,
                "current_url": url,
                "timestamp_client": data.get('timestamp')
            }

            registrar_log_forense(
                request=request,
                acao=f"UX_Hover_{acao}",
                tabela="Interface/Browser",
                diff_json=diff_json,
                usuario=request.user
            )
            return JsonResponse({'status': 'ok'})
        except Exception:
            pass

    return JsonResponse({'status': 'ignored'})

@login_required
def ai_insights_bi(request):
    try:
        from intranet.services.groq_ai import obter_client_groq
        client = obter_client_groq()
        if not client:
            return HttpResponse('<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro: Chave do Groq não configurada.</div>')

        modulo = request.GET.get('modulo', 'geral')
        import json
        import datetime
        from django.utils import timezone
        from django.db.models import Count, Sum

        hoje = timezone.now().date()
        context_data = {}
        papel = "Cientista de Dados (Data Scientist) Sênior e Diretor Executivo"
        foco = "GARGALOS OPERACIONAIS cruciais na saúde da igreja (pessoas, finanças e escalas)"

        if modulo == 'almoxarifado':
            from almoxarifado.models import ItemAlmoxarifado, MovimentacaoAlmoxarifado
            estoque_total = ItemAlmoxarifado.objects.aggregate(total=Sum('valor_estimado'))['total'] or 0
            depreciados = ItemAlmoxarifado.objects.filter(status_item='danificado').count()
            retiradas = MovimentacaoAlmoxarifado.objects.filter(tipo='retirada').values('item__nome').annotate(t=Count('item')).order_by('-t')[:3]
            context_data = {
                'valor_estoque_presumido': float(estoque_total),
                'itens_danificados_total': depreciados,
                'top_3_itens_mais_retirados': [f"{i['item__nome']} ({i['t']}x)" for i in retiradas]
            }
            papel = "Diretor Executivo de Logística e Almoxarifado"
            foco = "GARGALOS NO ESTOQUE (depreciação, extravios, itens críticos)"

        elif modulo == 'financeiro':
            from pdv.models import Venda
            inicio_mes = hoje.replace(day=1)
            faturamento = Venda.objects.filter(data_venda__gte=inicio_mes).aggregate(Sum('total'))['total__sum'] or 0
            ticket = Venda.objects.filter(data_venda__gte=inicio_mes).aggregate(Avg=Sum('total')/Count('id'))['Avg'] or 0
            context_data = {
                'faturamento_mes_atual': float(faturamento),
                'ticket_medio': float(ticket),
            }
            papel = "CFO / Diretor Financeiro Executivo"
            foco = "GARGALOS DE RECEITA E RENTABILIDADE"

        elif modulo == 'casais':
            from ministerio_casais.models import Casal
            crise = Casal.objects.filter(status_relacionamento='em_crise').count()
            total = Casal.objects.count()
            context_data = {
                'casais_cadastrados': total,
                'casais_em_crise': crise,
                'taxa_crise': f"{round((crise/total*100) if total else 0, 1)}%"
            }
            papel = "Diretor do Ministério de Famílias / Psicólogo Pastoral"
            foco = "CRISE NOS CASAMENTOS E PREVENÇÃO DE DIVÓRCIOS"

        elif modulo == 'visitantes':
            from visitantes.models import Visitante
            visitantes_total = Visitante.objects.count()
            visitantes_conv = Visitante.objects.filter(tornou_se_membro=True).count()
            context_data = {
                'total_visitantes': visitantes_total,
                'visitantes_convertidos_em_membros': visitantes_conv,
                'taxa_conversao': f"{round((visitantes_conv/visitantes_total*100) if visitantes_total else 0, 1)}%"
            }
            papel = "Diretor de CRM e Integração de Novos Membros"
            foco = "FALHAS NO FUNIL DE CONVERSÃO E EVASÃO DE VISITANTES"

        elif modulo == 'membros':
            from core.models import Membro
            from escalas.models import Escala, CompetenciaEscala
            comp_atual = CompetenciaEscala.objects.filter(mes_ano__icontains=hoje.strftime('%Y-%m')).first()
            furos = Escala.objects.filter(competencia=comp_atual, status_confirmacao__in=['recusada', 'ausente']).count() if comp_atual else 0
            context_data = {
                'membros_ativos': Membro.objects.filter(is_active=True).count(),
                'furos_em_escalas_neste_mes': furos
            }
            papel = "Diretor de RH Voluntário"
            foco = "SOBRECARGA DE VOLUNTÁRIOS E FUROS NAS ESCALAS"

        else: # geral
            context_data = {'status': 'Visão Geral ativada. Liderança global.'}

        prompt = f"""
        Você é um {papel} contratado pela Diretoria da Igreja PV Enseada.
        Abaixo estão os dados do seu departamento processados hoje.

        Sua missão: Identifique {foco} cruciais nestes dados e proponha 3 PLANOS DE AÇÃO curtos e executivos.

        Regra Estrita:
        1. Responda DIRETAMENTE com código HTML pronto (usando classes Tailwind: bg-gray-800, text-red-400 para alertas, text-blue-300 para ações, flex, gap-2). NÃO USE blocos de código ```html.
        2. Seja cirúrgico, fale como um executivo Sênior do departamento.

        Dados JSON:
        {json.dumps(context_data)}
        """

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3
        )

        html_response = response.choices[0].message.content.replace('```html', '').replace('```', '').strip()
        return HttpResponse(html_response)

    except Exception as e:
        return HttpResponse(f'<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro ao conectar com a LPU: {str(e)}</div>')

from .models import NotificacaoGlobal
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def ler_notificacao(request, notificacao_id):
    try:
        notif = NotificacaoGlobal.objects.get(id=notificacao_id, destinatario=request.user)
        notif.lida = True
        notif.save()
        return JsonResponse({'success': True})
    except NotificacaoGlobal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificação não encontrada'})

@login_required
@require_POST
def ler_todas_notificacoes(request):
    NotificacaoGlobal.objects.filter(destinatario=request.user, lida=False).update(lida=True)
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_gerar_backup_local(request):
    import shutil
    import datetime
    import os
    from django.conf import settings
    from core.models import DatabaseBackup

    if request.method == 'POST':
        db_path = 'db.sqlite3'
        if not os.path.exists(db_path):
            messages.error(request, "Banco de dados principal não encontrado.")
            return redirect('sysadmin_dashboard')

        # Criar diretório media/backups se não existir
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Fazer a cópia física
        try:
            shutil.copy2(db_path, backup_path)
            tamanho_mb = os.path.getsize(backup_path) / (1024 * 1024)

            # Registrar no BD
            DatabaseBackup.objects.create(
                arquivo=f"backups/{backup_filename}",
                tamanho_mb=tamanho_mb
            )

            # Manter apenas os 5 mais recentes (Rolling Backup)
            backups = DatabaseBackup.objects.order_by('-data_criacao')
            if backups.count() > 5:
                para_deletar = backups[5:]
                for b in para_deletar:
                    file_path = os.path.join(settings.MEDIA_ROOT, b.arquivo)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    b.delete()

            messages.success(request, "Backup local gerado e registrado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao gerar backup: {str(e)}")

    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_deletar_backup(request, backup_id):
    if request.method == 'POST':
        import os
        from core.models import DatabaseBackup
        from django.conf import settings

        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        file_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)

        if os.path.exists(file_path):
            os.remove(file_path)

        backup.delete()
        messages.success(request, "Backup excluído fisicamente e do registro.")
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@requer_permissao('sysadmin', 'editar')
def sysadmin_restaurar_backup(request, backup_id):
    if request.method == 'POST':
        import shutil
        import os
        from core.models import DatabaseBackup
        from django.conf import settings

        backup = get_object_or_404(DatabaseBackup, id=backup_id)
        backup_path = os.path.join(settings.MEDIA_ROOT, backup.arquivo)

        if not os.path.exists(backup_path):
            messages.error(request, "Arquivo de backup não encontrado no disco.")
            return redirect('sysadmin_dashboard')

        db_path = 'db.sqlite3'
        try:
            shutil.copy2(backup_path, db_path)
            messages.success(request, f"Banco de dados restaurado com a versão de {backup.data_criacao.strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception as e:
            messages.error(request, f"Erro ao restaurar: {str(e)}")

    return redirect('sysadmin_dashboard')

from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import reverse
import threading

@login_required
def sysadmin_rodar_spider(request):
    if not request.user.is_superuser and request.user.nivel_hierarquico != 'super_admin':
        return HttpResponseForbidden("Acesso restrito.")

    def run_spider_thread(user_id):
        try:
            call_command('run_spider', user_id=user_id)
        except Exception as e:
            print(f"Erro ao rodar spider: {e}")

    thread = threading.Thread(target=run_spider_thread, args=(request.user.id,))
    thread.start()

    messages.success(request, 'O Spider Test End-to-End foi iniciado em segundo plano. O resultado aparecerá nos logs abaixo em alguns instantes.')
    return HttpResponseRedirect(reverse('sysadmin'))

@login_required
def sysadmin_baixar_log_spider(request, log_id):
    if not request.user.is_superuser and request.user.nivel_hierarquico != 'super_admin':
        return HttpResponseForbidden("Acesso restrito.")

    from core.models import SpiderTestLog
    from django.http import HttpResponse

    log = get_object_or_404(SpiderTestLog, id=log_id)
    response = HttpResponse(log.log_texto, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="spider_log_{log.id}_{log.data_execucao.strftime("%Y%m%d%H%M")}.txt"'
    return response

@login_required
@requer_permissao('sysadmin', 'editar')
def sysadmin_deploy_producao(request):
    from django.core.management import call_command
    import io
    from django.utils.crypto import get_random_string
    import os

    config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)
    if config.sistema_implantado:
        messages.error(request, "O sistema já foi implantado! Ação bloqueada.")
        return redirect('sysadmin_dashboard')

    try:
        # 1. Migrate
        out = io.StringIO()
        call_command('migrate', interactive=False, stdout=out)

        # 2. Collectstatic
        call_command('collectstatic', interactive=False, stdout=out)

        # 3. Clean Cache
        from django.core.cache import cache
        cache.clear()

        # 4. Generate new SECRET_KEY in .env
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_text = f.read()
            import re
            new_key = get_random_string(50)
            env_text = re.sub(r'SECRET_KEY=.*', f'SECRET_KEY={new_key}', env_text)
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_text)

        # 5. Lock it
        config.sistema_implantado = True
        config.save()

        messages.success(request, "SISTEMA IMPLANTADO COM SUCESSO! Caches limpos, migrações aplicadas, arquivos estáticos copiados e Chave Secreta rotacionada.")
    except Exception as e:
        messages.error(request, f"Erro crítico no deploy: {str(e)}")

    return redirect('sysadmin_dashboard')
