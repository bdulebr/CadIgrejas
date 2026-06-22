import os
import sys

views_path = r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\views.py'

with open(views_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("def dashboard_view(request):"):
        skip = True
        
        # Inject our new dashboard_view
        new_lines.append(
"""def dashboard_view(request):
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
"""
        )
    elif skip and line.startswith("def perfil_view(request):"):
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open(views_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
