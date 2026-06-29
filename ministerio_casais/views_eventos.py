from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from permissoes.decorators import requer_permissao
from django.contrib import messages
from django.utils import timezone
from .models import EventoCasal, Casal, LoteEvento, InscricaoEvento, PagamentoInscricaoEvento
from django.db.models import Sum, Count

@login_required
@requer_permissao('casais', 'ver')
def dashboard_eventos(request):
    eventos_abertos = EventoCasal.objects.filter(status__in=['Planejamento', 'Aberto', 'Lotado']).order_by('data_inicio')
    eventos_encerrados = EventoCasal.objects.filter(status='Encerrado').order_by('-data_inicio')[:10]

    context = {
        'eventos_abertos': eventos_abertos,
        'eventos_encerrados': eventos_encerrados,
    }
    return render(request, 'ministerio_casais/eventos/dashboard.html', context)

@login_required
@requer_permissao('casais', 'editar')
def criar_evento(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        tipo = request.POST.get('tipo')
        status = request.POST.get('status')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim') or None
        local = request.POST.get('local')
        capacidade_maxima = request.POST.get('capacidade_maxima')
        valor_base = request.POST.get('valor_base') or 0
        descricao = request.POST.get('descricao')

        evento = EventoCasal.objects.create(
            titulo=titulo,
            tipo=tipo,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
            local=local,
            capacidade_maxima=capacidade_maxima,
            valor_base=valor_base,
            descricao=descricao
        )
        messages.success(request, 'Evento criado com sucesso!')
        return redirect('painel_evento', evento_id=evento.id)

    return redirect('dashboard_eventos_casais')

@login_required
@requer_permissao('casais', 'ver')
def painel_evento(request, evento_id):
    evento = get_object_or_404(EventoCasal, id=evento_id)
    inscricoes = evento.inscricoes.all().order_by('-data_inscricao')
    lotes = evento.lotes.all().order_by('valor')

    # Resumo Financeiro do Evento
    total_arrecadado = PagamentoInscricaoEvento.objects.filter(inscricao__evento=evento).aggregate(total=Sum('valor_pago'))['total'] or 0
    total_esperado = inscricoes.aggregate(total=Sum('valor_total_devido'))['total'] or 0

    casais_nao_inscritos = Casal.objects.exclude(id__in=inscricoes.values_list('casal_id', flat=True)).filter(arquivado=False)

    context = {
        'evento': evento,
        'inscricoes': inscricoes,
        'lotes': lotes,
        'total_arrecadado': total_arrecadado,
        'total_esperado': total_esperado,
        'casais_nao_inscritos': casais_nao_inscritos,
        'vagas_restantes': evento.capacidade_maxima - inscricoes.count()
    }
    return render(request, 'ministerio_casais/eventos/painel_evento.html', context)

@login_required
@requer_permissao('casais', 'editar')
def adicionar_lote(request, evento_id):
    evento = get_object_or_404(EventoCasal, id=evento_id)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        valor = request.POST.get('valor')
        data_limite = request.POST.get('data_limite') or None

        LoteEvento.objects.create(
            evento=evento,
            nome=nome,
            valor=valor,
            data_limite=data_limite
        )
        messages.success(request, 'Lote adicionado com sucesso!')
    return redirect('painel_evento', evento_id=evento.id)

@login_required
@requer_permissao('casais', 'editar')
def inscrever_casal_evento(request, evento_id):
    evento = get_object_or_404(EventoCasal, id=evento_id)
    if request.method == 'POST':
        casal_id = request.POST.get('casal_id')
        lote_id = request.POST.get('lote_id')
        quarto = request.POST.get('quarto')
        observacoes = request.POST.get('observacoes')

        casal = get_object_or_404(Casal, id=casal_id)
        lote = LoteEvento.objects.filter(id=lote_id).first() if lote_id else None

        # Check se já não está inscrito
        if InscricaoEvento.objects.filter(evento=evento, casal=casal).exists():
            messages.error(request, 'Este casal já está inscrito neste evento.')
            return redirect('painel_evento', evento_id=evento.id)

        InscricaoEvento.objects.create(
            evento=evento,
            casal=casal,
            lote=lote,
            quarto=quarto,
            observacoes_medicas=observacoes
        )
        messages.success(request, 'Casal inscrito com sucesso!')

    return redirect('painel_evento', evento_id=evento.id)

@login_required
@requer_permissao('casais', 'editar')
def adicionar_pagamento_inscricao(request, inscricao_id):
    inscricao = get_object_or_404(InscricaoEvento, id=inscricao_id)
    if request.method == 'POST':
        valor_pago = request.POST.get('valor_pago')
        forma_pagamento = request.POST.get('forma_pagamento')

        if valor_pago:
            try:
                valor_pago = float(valor_pago.replace(',', '.'))
                PagamentoInscricaoEvento.objects.create(
                    inscricao=inscricao,
                    valor_pago=valor_pago,
                    forma_pagamento=forma_pagamento
                )

                # Recalcula o total pago e atualiza status
                total_pago = inscricao.pagamentos.aggregate(total=Sum('valor_pago'))['total'] or 0
                if total_pago >= inscricao.valor_total_devido:
                    inscricao.status_pagamento = 'Pago'
                else:
                    inscricao.status_pagamento = 'Parcial'
                inscricao.save()

                messages.success(request, 'Pagamento registrado com sucesso!')
            except ValueError:
                messages.error(request, 'Valor de pagamento inválido.')

    return redirect('painel_evento', evento_id=inscricao.evento.id)

@login_required
@requer_permissao('casais', 'ver')
def lista_presenca_pdf(request, evento_id):
    from io import BytesIO
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    import xhtml2pdf.pisa as pisa

    evento = get_object_or_404(EventoCasal, id=evento_id)
    inscricoes = evento.inscricoes.all().order_by('casal__nome_conjuge_1')

    html_str = render_to_string('ministerio_casais/eventos/pdf_lista_presenca.html', {
        'evento': evento,
        'inscricoes': inscricoes,
        'data_geracao': timezone.now()
    })

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="lista_presenca_{evento.id}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
