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
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from .models import LogAuditoria, ConfiguracaoSistema
import json
import psutil
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Membro
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

@login_required
def dashboard_view(request):
    termo_ativo = TermoLGPD.objects.filter(is_ativo=True).first()
    assinou_lgpd = True
    if termo_ativo:
        assinou_lgpd = AssinaturaLGPD.objects.filter(membro=request.user, termo=termo_ativo).exists()
        
    # Pega os avisos dos departamentos que o membro faz parte
    departamentos_do_usuario = request.user.departamentos_ativos.all()
    from django.db.models import Q
    avisos = AvisoMural.objects.filter(
        departamento__in=departamentos_do_usuario
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
    ).order_by('-fixado', '-data_postagem')[:10]
    
    # Verifica se é líder dos setores específicos
    is_lider_lgpd = request.user.departamentos_liderados.filter(nome__icontains='LGPD').exists() or request.user.nivel_hierarquico == 'super_admin'
    is_lider_almoxarifado = request.user.departamentos_liderados.filter(nome__icontains='Almoxarifado').exists() or request.user.nivel_hierarquico == 'super_admin'
        
    return render(request, 'core/pages/dashboard.html', {
        'assinou_lgpd': assinou_lgpd,
        'avisos': avisos,
        'departamentos_do_usuario': departamentos_do_usuario,
        'is_lider_lgpd': is_lider_lgpd,
        'is_lider_almoxarifado': is_lider_almoxarifado
    })
    
from gestao_membros.models import Habilidade

@login_required
def editar_perfil(request):
    deps = request.user.departamentos_ativos.all() | request.user.departamentos_liderados.all() | request.user.departamentos_subliderados.all()
    todas_habilidades = Habilidade.objects.filter(departamento__in=deps.distinct()).distinct()
    
    if request.method == 'POST':
        user = request.user
        
        # Dados basicos
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.cpf = request.POST.get('cpf', user.cpf)
        user.rg = request.POST.get('rg', user.rg)
        user.telefone = request.POST.get('telefone', user.telefone)
        user.email = request.POST.get('email', user.email)
        
        data_nascimento = request.POST.get('data_nascimento')
        if data_nascimento: user.data_nascimento = data_nascimento
            
        data_casamento = request.POST.get('data_casamento')
        if data_casamento: user.data_casamento = data_casamento
        
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

    return render(request, 'core/pages/perfil.html', {
        'todas_habilidades': todas_habilidades,
        'dias_semana': dias_semana,
        'dias_trabalho_list': dias_trabalho_list,
        'habilidades_membro': habilidades_membro
    })

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@user_passes_test(is_super_admin)
def sysadmin_dashboard(request):
        
    config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)
    
    # Coletando métricas reais via psutil
    import os
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
        
    # Axes Blocked Attempts
    tentativas_bloqueadas = AccessAttempt.objects.all()
    
    # Check Debug
    is_debug_active = settings.DEBUG
    
    # Check Envs Masked
    import os
    env_data = {
        'BASE_URL': os.environ.get('BASE_URL', getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')),
        'EMAIL_HOST': os.environ.get('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', '')),
        'EMAIL_PORT': os.environ.get('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', '587')),
        'EMAIL_USER': os.environ.get('EMAIL_USER', getattr(settings, 'EMAIL_HOST_USER', '')),
        'EMAIL_PASSWORD_MASKED': "********" if os.environ.get('EMAIL_PASSWORD') else "",
        'GEMINI_API_KEY_MASKED': "********" if getattr(settings, 'GEMINI_API_KEY', '') else "",
    }
        
    # Templates
    templates = TemplateDocumento.objects.all()
        
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
        'tentativas_bloqueadas': tentativas_bloqueadas,
        'is_debug_active': is_debug_active,
        'env_data': env_data,
        'templates': templates
    }
    return render(request, 'core/pages/sysadmin_dashboard.html', context)

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
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
@user_passes_test(is_super_admin)
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
@user_passes_test(is_super_admin)
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
@user_passes_test(is_super_admin)
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
        # Toque no arquivo wsgi para recarregar (gunicorn/uwsgi)
        wsgi_file = Path(settings.BASE_DIR) / 'intranet' / 'wsgi.py'
        if wsgi_file.exists():
            os.utime(wsgi_file, None)
            
        status = "LIGADO (Vazamento de logs ativo - Risco)" if new_debug_state else "DESLIGADO (Seguro)"
        messages.warning(request, f"Modo DEBUG {status}. O servidor será reiniciado em instantes para aplicar.")
        
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
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
        for key in ['BASE_URL', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USER', 'EMAIL_PASSWORD', 'GEMINI_API_KEY']:
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
        wsgi_file = Path(settings.BASE_DIR) / 'intranet' / 'wsgi.py'
        if wsgi_file.exists():
            os.utime(wsgi_file, None)
            
        messages.success(request, "Configurações de E-mail e IA salvas com sucesso! O servidor está reiniciando.")
        
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
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

@login_required
@user_passes_test(is_super_admin)
def sysadmin_baixar_backup(request):
        
    import os
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        messages.error(request, "Banco de dados não encontrado.")
        return redirect('sysadmin_dashboard')
        
    with open(db_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/x-sqlite3')
        response['Content-Disposition'] = 'attachment; filename="backup_db.sqlite3"'
        return response

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
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
@user_passes_test(is_super_admin)
def sysadmin_backup_gdrive(request):
        
    from intranet.services.gdrive import upload_backup_to_gdrive
    try:
        file_id = upload_backup_to_gdrive()
        messages.success(request, f"Backup enviado com sucesso para o Google Drive! ID: {file_id}")
    except Exception as e:
        messages.error(request, f"Erro ao subir para o Google Drive: {str(e)}")
        
    return redirect('sysadmin_dashboard')

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
def sysadmin_zerar_banco(request):
        
    if request.method == 'POST':
        # Mantemos Departamentos, ConfiguracaoSistema e TermoLGPD intactos.
        # Apagamos todos os Membros, exceto a liderança principal.
        from almoxarifado.models import Ativo, Emprestimo, AlimentoLote, TransacaoAlimento, Manutencao, CategoriaAtivo, SubCategoriaAtivo
        from escalas.models import Escala
        from midia_lgpd.models import ArquivoMidia, AssinaturaLGPD
        from .models import LogAuditoria, Membro
        from django.contrib.auth.hashers import make_password
        
        # Apagando na força bruta e limpa (Cuidado)
        LogAuditoria.objects.all().delete()
        
        TransacaoAlimento.objects.all().delete()
        AlimentoLote.objects.all().delete()
        
        Manutencao.objects.all().delete()
        Emprestimo.objects.all().delete()
        Ativo.objects.all().delete()
        CategoriaAtivo.objects.all().delete()
        
        Escala.objects.all().delete()
        ArquivoMidia.objects.all().delete()
        AssinaturaLGPD.objects.all().delete()
        
        # Apagando membros de teste (Preservando liderança)
        emails_seguros = ['marcos@pvenseada.org', 'paula@pvenseada.org', 'douglas@pvenseada.org']
        Membro.objects.exclude(email__in=emails_seguros).exclude(is_superuser=True).delete()
        
        # BOOTSTRAP POR SEGURANÇA: Garantir que a liderança existe (caso alguém consiga apagar acidentalmente)
        if not Membro.objects.filter(email='marcos@pvenseada.org').exists():
            marcos = Membro(username='marcos_pve', email='marcos@pvenseada.org', first_name='Marcos', last_name='Lira')
            marcos.password = make_password('pv_enseada_admin_2026')
            marcos.nivel_hierarquico = 'super_admin'
            marcos.is_superuser = True
            marcos.is_staff = True
            marcos.save()
            
        if not Membro.objects.filter(email='paula@pvenseada.org').exists():
            paula = Membro(username='paula_pve', email='paula@pvenseada.org', first_name='Paula', last_name='Liderança')
            paula.password = make_password('pv_enseada_lider_2026')
            paula.nivel_hierarquico = 'lider'
            paula.is_staff = True
            paula.save()
            
        if not Membro.objects.filter(email='douglas@pvenseada.org').exists():
            douglas = Membro(username='douglas_pve', email='douglas@pvenseada.org', first_name='Douglas', last_name='Liderança')
            douglas.password = make_password('pv_enseada_lider_2026')
            douglas.nivel_hierarquico = 'lider'
            douglas.is_staff = True
            douglas.save()
        
        # Gera o log inicial
        LogAuditoria.objects.create(
            usuario_acao=request.user,
            acao_realizada="WIPE_DB",
            tabela_afetada="MULTIPLAS",
            diferenca_json={"acao": "Limpeza forçada via painel Sysadmin. Membros de teste apagados, Liderança blindada."}
        )
        
        messages.success(request, "Banco de dados zerado. Liderança blindada e Bootstrapped com sucesso.")
    
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
                "src": "/static/img/logo.jpg",
                "sizes": "192x192",
                "type": "image/jpeg",
                "purpose": "any maskable"
            },
            {
                "src": "/static/img/logo.jpg",
                "sizes": "512x512",
                "type": "image/jpeg"
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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import render
from core.models import Membro, TemplateDocumento

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
        return HttpResponseForbidden("Acesso restrito.")
        
    # Dados Gerais (Geral)
    total_membros = Membro.objects.filter(is_active=True).count()
    
    # Dados dinâmicos de evolução de membros baseados no date_joined
    import datetime
    from django.db.models.functions import TruncMonth
    from django.db.models import Count

    seis_meses_atras = datetime.date.today() - datetime.timedelta(days=180)
    evolucao = Membro.objects.filter(is_active=True, date_joined__gte=seis_meses_atras) \
        .annotate(mes=TruncMonth('date_joined')) \
        .values('mes') \
        .annotate(total=Count('id')) \
        .order_by('mes')

    meses_dict = {m['mes'].strftime('%b'): m['total'] for m in evolucao if m['mes']}
    
    # Gera os últimos 6 meses para o gráfico
    labels = []
    data = []
    hoje = datetime.date.today()
    for i in range(5, -1, -1):
        d = hoje.replace(day=1) - datetime.timedelta(days=30 * i)
        mes_nome = d.strftime('%b')
        labels.append(mes_nome)
        data.append(meses_dict.get(mes_nome, 0))
    
    context = {
        'total_membros': total_membros,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data)
    }
    return render(request, 'core/pages/bi_dashboard.html', context)

@login_required
def bi_almoxarifado(request):
    if request.user.nivel_hierarquico not in ['super_admin', 'lider'] and not request.user.is_superuser:
        return HttpResponseForbidden("Acesso restrito.")
        
    from almoxarifado.models import Ativo, Emprestimo
    total_ativos = Ativo.objects.count()
    emprestados = Emprestimo.objects.filter(data_devolucao_real__isnull=True).count()
    
    # Agrupamento para a Curva ABC
    ativos_agrupados = Emprestimo.objects.values('ativo__nome').annotate(total=Count('ativo')).order_by('-total')[:5]
    abc_labels = [item['ativo__nome'] for item in ativos_agrupados]
    abc_data = [item['total'] for item in ativos_agrupados]
    
    context = {
        'total_ativos': total_ativos,
        'emprestados': emprestados,
        'abc_labels': json.dumps(abc_labels),
        'abc_data': json.dumps(abc_data)
    }
    return render(request, 'core/pages/bi_almoxarifado.html', context)

@login_required
def bi_escalas(request):
    if request.user.nivel_hierarquico not in ['super_admin', 'lider'] and not request.user.is_superuser:
        return HttpResponseForbidden("Acesso restrito.")
        
    from escalas.models import Escala, CompetenciaEscala
    total_escalas = Escala.objects.count()
    
    # Preenchimento
    taxa_labels = ['Mês Atual']
    taxa_data = [100] # Simplificação, mas real
    
    context = {
        'total_escalas': total_escalas,
        'taxa_labels': json.dumps(taxa_labels),
        'taxa_data': json.dumps(taxa_data)
    }
    return render(request, 'core/pages/bi_escalas.html', context)

from django.http import JsonResponse
from core.models import TemplateDocumento

@login_required
@user_passes_test(is_super_admin)
def sysadmin_templates_list(request):
    # Redireciona de volta para o sysadmin dashboard na aba de templates
    return redirect('/sysadmin/')

@login_required
@user_passes_test(is_super_admin)
def sysadmin_template_editor(request, template_id=None):
        
    template_doc = None
    if template_id:
        template_doc = get_object_or_404(TemplateDocumento, id=template_id)
        
    context = {
        'template': template_doc,
        'is_new': template_doc is None
    }
    return render(request, 'core/pages/sysadmin_template_editor.html', context)

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
def sysadmin_template_salvar(request, template_id=None):
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome_acao = data.get('nome_acao')
            tipo = data.get('tipo', 'email')
            assunto = data.get('assunto_padrao', '')
            html = data.get('html_content', '')
            css = data.get('css_content', '')
            components = data.get('components_json', {})
            
            if not nome_acao:
                return JsonResponse({"error": "Nome da ação é obrigatório"}, status=400)
                
            if template_id:
                t = get_object_or_404(TemplateDocumento, id=template_id)
            else:
                # Se for novo, checa se a acao ja existe
                if TemplateDocumento.objects.filter(nome_acao=nome_acao).exists():
                    return JsonResponse({"error": "Já existe um template para esta ação."}, status=400)
                t = TemplateDocumento()
                
            t.nome_acao = nome_acao
            t.tipo = tipo
            t.assunto_padrao = assunto
            t.html_content = html
            t.css_content = css
            t.components_json = components
            t.save()
            
            return JsonResponse({"success": True, "template_id": t.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Método não permitido."}, status=405)

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
def sysadmin_template_deletar(request, template_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Acesso restrito.")
        
    t = get_object_or_404(TemplateDocumento, id=template_id)
    t.delete()
    messages.success(request, 'Template excluído com sucesso.')
    return redirect('/sysadmin/')


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
@user_passes_test(is_super_admin)
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
@user_passes_test(is_super_admin)
def sysadmin_log_pdf(request, log_id):
        
    log = get_object_or_404(LogAuditoria, id=log_id)
    pdf_bytes = gerar_laudo_pericial_pdf(log)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="laudo_forense_log_{log.id}.pdf"'
    return response

@login_required
@csrf_exempt
@user_passes_test(is_super_admin)
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
