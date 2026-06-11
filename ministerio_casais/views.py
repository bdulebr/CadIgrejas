from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Casal, HistoricoAconselhamentoCasal, CursoCasal, MatriculaCursoCasal, EventoCasal, PresencaEventoCasal
import os
from django.conf import settings
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string

def check_permission(user):
    # Regra Zero-Trust: Apenas Super Admin ou líder do ministério de casais pode ver
    return user.nivel_hierarquico == 'super_admin' or user.departamento_responsavel and 'casal' in user.departamento_responsavel.nome.lower()

@login_required
def dashboard_casais(request):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado. Este módulo contém informações confidenciais.", status=403)

    casais = Casal.objects.all().order_by('-data_cadastro')

    # Termômetro (Crise vs Saudável)
    # Vamos contar quantos aconselhamentos tiveram nivel >= 4 nos ultimos 30 dias
    trinta_dias_atras = timezone.now() - timezone.timedelta(days=30)
    alertas_vermelhos = HistoricoAconselhamentoCasal.objects.filter(nivel_crise__gte=4, data_sessao__gte=trinta_dias_atras).values('casal').distinct().count()

    # Aniversários de Casamento (Bodas) no mês atual
    mes_atual = timezone.now().month
    bodas_mes = Casal.objects.filter(data_aniversario_casamento__month=mes_atual).count()

    # Cursos e Eventos
    total_cursos = CursoCasal.objects.count()
    total_casais = casais.count()

    # Trilha de Noivos ativos
    noivos_na_trilha = Casal.objects.filter(status_relacionamento='Noivos', trilha_noivos_etapa__gt=0).count()

    context = {
        'casais': casais,
        'total_casais': total_casais,
        'alertas_vermelhos': alertas_vermelhos,
        'bodas_mes': bodas_mes,
        'total_cursos': total_cursos,
        'noivos_na_trilha': noivos_na_trilha,
    }
    return render(request, 'ministerio_casais/dashboard.html', context)

@login_required
def perfil_casal(request, casal_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    casal = get_object_or_404(Casal, id=casal_id)
    historico = casal.historicos_aconselhamento.all().order_by('-data_sessao')
    matriculas = casal.matriculas_cursos.all()

    context = {
        'casal': casal,
        'historico': historico,
        'matriculas': matriculas,
    }
    return render(request, 'ministerio_casais/perfil.html', context)

@login_required
def exportar_certificados(request, matricula_id):
    if not check_permission(request.user):
        return HttpResponse("Acesso Negado.", status=403)

    matricula = get_object_or_404(MatriculaCursoCasal, id=matricula_id)

    from core.models import ConfiguracaoSistema
    sys_config = ConfiguracaoSistema.objects.first()
    if sys_config and sys_config.igreja_logo:
        logo_path = sys_config.igreja_logo.path
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')

    html_str = render_to_string('ministerio_casais/pdf_certificado.html', {
        'matricula': matricula,
        'data_geracao': timezone.now(),
        'logo_path': logo_path
    })

    result = BytesIO()
    import xhtml2pdf.pisa as pisa
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificado_{matricula.casal.id}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
