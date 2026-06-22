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

        # Fast-track PIN PDV login
        if len(username) == 4 and username.isdigit() and not password:
            from core.models import Membro
            membro = Membro.objects.filter(pin_pdv=username, is_active=True).first()
            if membro:
                membro.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, membro)
                return redirect('pdv_frente_caixa')
            else:
                messages.error(request, 'PIN Inválido ou Usuário sem permissão para o PDV.')
                return redirect('login')

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
    ).order_by('-fixado', '-data_postagem')[:5]

    # Verifica permissões específicas
    is_lider_lgpd = request.user.departamentos_liderados.filter(nome__icontains='LGPD').exists() or request.user.nivel_hierarquico == 'super_admin'
    is_lider_almoxarifado = request.user.departamentos_liderados.filter(nome__icontains='Almoxarifado').exists() or request.user.nivel_hierarquico == 'super_admin'
    
    # Próxima escala do usuário
    from escalas.models import Escala, CultoEvento
    from datetime import date
    minha_proxima_escala = Escala.objects.filter(membro=request.user, data__gte=date.today()).order_by('data').first()
    
    # Próximos 4 cultos gerais (mesmo sem estar escalado)
    proximos_cultos = CultoEvento.objects.filter(data__gte=date.today()).order_by('data')[:4]
    
    # Notícias Ticker Globais
    from .models import NoticiaTicker
    noticias_ticker = NoticiaTicker.objects.filter(ativo=True).order_by('-data_criacao')[:5]
    
    # IA Insight
    insight_ia = gerar_insight_ia(request.user)

    return render(request, 'core/pages/dashboard.html', {
        'assinou_lgpd': assinou_lgpd,
        'avisos': avisos,
        'departamentos_do_usuario': departamentos_do_usuario,
        'is_lider_lgpd': is_lider_lgpd,
        'is_lider_almoxarifado': is_lider_almoxarifado,
        'is_lider_pdv': True, # Hardcoded cause they use config now
        'minha_proxima_escala': minha_proxima_escala,
        'proximos_cultos': proximos_cultos,
        'noticias_ticker': noticias_ticker,
        'insight_ia': insight_ia
    })

# ==========================================
# PWA VIEWS (RECOVERED)
# ==========================================
def pwa_manifest(request):
    return render(request, 'core/manifest.json', content_type='application/json')

def pwa_service_worker(request):
    return render(request, 'core/sw.js', content_type='application/javascript')
