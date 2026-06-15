from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from .models import Lancamento, AnexoLancamento, CategoriaTesouraria, TagTesouraria, ConfiguracaoTesouraria
from .forms import LancamentoForm
from core.models import LogImutavel
from gestao_membros.models import Departamento
import datetime
import calendar
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from intranet.services.gemini_ai import analisar_comprovante_tesouraria, gerar_planilha_sede_mensal, analisar_planilha_importacao
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
# Decorator de segurança militar
def tesouraria_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.nivel_hierarquico == 'super_admin':
            return view_func(request, *args, **kwargs)

        is_leader = request.user.departamentos_liderados.filter(nome__icontains='Tesouraria').exists()

        if is_leader:
            return view_func(request, *args, **kwargs)

        LogImutavel.objects.create(
            membro=request.user,
            acao="ACESSO_NEGADO_TESOURARIA",
            dados_acao="Tentativa de acessar rota protegida da Tesouraria sem privilégios de Líder."
        )
        raise PermissionDenied("Acesso restrito: Apenas o Líder da Tesouraria e o Super Admin possuem acesso.")
    return _wrapped_view

@login_required
@tesouraria_required
def dashboard(request):
    mes_atual = datetime.date.today().month
    ano_atual = datetime.date.today().year

    lancamentos_mes = Lancamento.objects.filter(data_vencimento__month=mes_atual, data_vencimento__year=ano_atual, is_active=True, status='pago')

    entradas = lancamentos_mes.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or 0
    saidas = lancamentos_mes.filter(tipo='saida').aggregate(total=Sum('valor'))['total'] or 0
    saldo = entradas - saidas

    context = {
        'entradas': entradas,
        'saidas': saidas,
        'saldo': saldo,
        'mes_atual': mes_atual,
        'ano_atual': ano_atual
    }
    return render(request, 'tesouraria/dashboard.html', context)

@login_required
@tesouraria_required
def lista_lancamentos(request):
    query = request.GET.get('q', '')
    tipo_filtro = request.GET.get('tipo', '')
    mes = request.GET.get('mes', '')

    lancamentos = Lancamento.objects.filter(is_active=True)

    if query:
        lancamentos = lancamentos.filter(
            Q(descricao__icontains=query) |
            Q(categoria__nome__icontains=query) |
            Q(observacoes__icontains=query) |
            Q(tags__nome__icontains=query)
        ).distinct()

    if tipo_filtro:
        lancamentos = lancamentos.filter(tipo=tipo_filtro)

    if mes:
        lancamentos = lancamentos.filter(data_vencimento__month=mes)

    paginator = Paginator(lancamentos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tesouraria/lista_lancamentos.html', {'page_obj': page_obj, 'query': query})

@login_required
@tesouraria_required
def novo_lancamento(request):
    if request.method == 'POST':
        form = LancamentoForm(request.POST)
        files = request.FILES.getlist('anexos')
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.responsavel = request.user
            lancamento.save()
            form.save_m2m() # Salvar tags

            # Salvar infinitos anexos
            for f in files:
                AnexoLancamento.objects.create(lancamento=lancamento, arquivo=f, nome_original=f.name)

            messages.success(request, 'Lançamento registrado com segurança militar.')
            return redirect('tesouraria:lista_lancamentos')
    else:
        form = LancamentoForm()

    return render(request, 'tesouraria/form_lancamento.html', {'form': form, 'title': 'Novo Lançamento'})

@login_required
@tesouraria_required
def detalhe_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    return render(request, 'tesouraria/detalhe_lancamento.html', {'lancamento': lancamento})

@login_required
@tesouraria_required
def cancelar_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        # Checagem de 48h
        from django.utils import timezone
        limite_horas = 48
        diferenca = timezone.now() - lancamento.criado_em

        if diferenca.total_seconds() > (limite_horas * 3600) and request.user.nivel_hierarquico != 'super_admin':
            LogImutavel.objects.create(membro=request.user, acao="TENTATIVA_ESTORNO_NEGADA", dados_acao=f"Tentou estornar Lançamento {lancamento.id} após {limite_horas}h.")
            messages.error(request, f"Segurança Zero-Trust: Lançamentos não podem ser estornados após {limite_horas} horas. Apenas o Administrador Global pode realizar esta ação.")
            return redirect('tesouraria:detalhe_lancamento', pk=pk)

        motivo = request.POST.get('motivo', 'Sem motivo')
        # Soft delete / Cancelamento com log imutável severo
        lancamento.status = 'cancelado'
        lancamento.observacoes += f"\\n[CANCELADO POR {request.user.username}]: {motivo}"
        lancamento.is_active = False
        lancamento.save()

        LogImutavel.objects.create(
            membro=request.user,
            acao=f"CANCELOU_LANCAMENTO_{lancamento.id}",
            dados_acao=f"Motivo fornecido: {motivo} | Valor: {lancamento.valor}"
        )
        messages.warning(request, 'Lançamento cancelado e auditado com sucesso.')
        return redirect('tesouraria:lista_lancamentos')
    return redirect('tesouraria:detalhe_lancamento', pk=pk)

# Views de Exportação
import csv
from django.http import HttpResponse


import openpyxl
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.dateparse import parse_date

@login_required
@tesouraria_required
def exportar_relatorio(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    formato = request.GET.get('formato', 'csv')

    lancamentos = Lancamento.objects.filter(is_active=True).order_by('data_vencimento')

    if data_inicio:
        dt_inicio = parse_date(data_inicio)
        if dt_inicio:
            lancamentos = lancamentos.filter(data_vencimento__gte=dt_inicio)

    if data_fim:
        dt_fim = parse_date(data_fim)
        if dt_fim:
            lancamentos = lancamentos.filter(data_vencimento__lte=dt_fim)

    if formato == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="relatorio_tesouraria_{datetime.date.today()}.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Lançamentos"

        # Cabeçalhos
        headers = ['ID', 'Data', 'Tipo', 'Descrição', 'Categoria', 'Tags', 'Status', 'Valor (R$)']
        ws.append(headers)

        total_entradas = 0
        total_saidas = 0

        for l in lancamentos:
            tags = ", ".join([t.nome for t in l.tags.all()])
            ws.append([
                l.id,
                l.data_vencimento.strftime('%d/%m/%Y'),
                l.get_tipo_display(),
                l.descricao,
                l.categoria.nome,
                tags,
                l.get_status_display(),
                float(l.valor)
            ])
            if l.status == 'pago':
                if l.tipo == 'entrada':
                    total_entradas += float(l.valor)
                else:
                    total_saidas += float(l.valor)

        ws.append([])
        ws.append(['', '', '', '', '', '', 'TOTAL ENTRADAS', total_entradas])
        ws.append(['', '', '', '', '', '', 'TOTAL SAÍDAS', total_saidas])
        ws.append(['', '', '', '', '', '', 'SALDO', total_entradas - total_saidas])

        wb.save(response)
        return response

    elif formato == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_tesouraria_{datetime.date.today()}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"Relatório de Tesouraria - Gerado em {datetime.date.today().strftime('%d/%m/%Y')}", styles['Title']))
        elements.append(Spacer(1, 12))

        data = [['Data', 'Tipo', 'Descrição', 'Categoria', 'Status', 'Valor']]

        total_entradas = 0
        total_saidas = 0

        for l in lancamentos:
            data.append([
                l.data_vencimento.strftime('%d/%m/%Y'),
                l.get_tipo_display(),
                l.descricao[:30] + '...' if len(l.descricao) > 30 else l.descricao,
                l.categoria.nome,
                l.get_status_display(),
                f"R$ {l.valor:.2f}"
            ])
            if l.status == 'pago':
                if l.tipo == 'entrada':
                    total_entradas += float(l.valor)
                else:
                    total_saidas += float(l.valor)

        data.append(['', '', '', '', 'ENTRADAS', f"R$ {total_entradas:.2f}"])
        data.append(['', '', '', '', 'SAÍDAS', f"R$ {total_saidas:.2f}"])
        data.append(['', '', '', '', 'SALDO GERAL', f"R$ {total_entradas - total_saidas:.2f}"])

        table = Table(data, colWidths=[70, 60, 200, 150, 80, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Cores para saldo
            ('BACKGROUND', (-2, -3), (-1, -1), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
        ]))

        elements.append(table)
        doc.build(elements)
        return response

    else: # default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tesouraria_{datetime.date.today()}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Data', 'Tipo', 'Descrição', 'Categoria', 'Status', 'Valor (R$)'])

        total_entradas = 0
        total_saidas = 0
        for l in lancamentos:
            writer.writerow([l.id, l.data_vencimento.strftime('%d/%m/%Y'), l.get_tipo_display(), l.descricao, l.categoria.nome, l.get_status_display(), l.valor])
            if l.status == 'pago':
                if l.tipo == 'entrada':
                    total_entradas += float(l.valor)
                else:
                    total_saidas += float(l.valor)

        writer.writerow([])
        writer.writerow(['', '', '', '', '', 'SALDO GERAL', total_entradas - total_saidas])
        return response

@login_required
@tesouraria_required
def configuracoes_tesouraria(request):
    categorias = CategoriaTesouraria.objects.all().order_by('tipo', 'nome')
    tags = TagTesouraria.objects.all().order_by('nome')
    config_sede, _ = ConfiguracaoTesouraria.objects.get_or_create(id=1)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_categoria':
            nome = request.POST.get('nome')
            tipo = request.POST.get('tipo')
            if nome and tipo:
                CategoriaTesouraria.objects.create(nome=nome, tipo=tipo)
                messages.success(request, f"Categoria '{nome}' criada com sucesso.")

        elif action == 'add_tag':
            nome = request.POST.get('nome')
            if nome:
                TagTesouraria.objects.create(nome=nome)
                messages.success(request, f"Tag '#{nome}' criada com sucesso.")

        elif action == 'del_categoria':
            cat_id = request.POST.get('cat_id')
            cat = get_object_or_404(CategoriaTesouraria, id=cat_id)
            if not cat.lancamentos.exists():
                cat.delete()
                messages.warning(request, "Categoria excluída.")
            else:
                messages.error(request, "Erro: Categoria está em uso por lançamentos.")

        elif action == 'del_tag':
            tag_id = request.POST.get('tag_id')
            tag = get_object_or_404(TagTesouraria, id=tag_id)
            tag.delete()
            messages.warning(request, "Tag excluída.")

        elif action == 'save_sede':
            config_sede.email_sede = request.POST.get('email_sede', '')
            config_sede.nome_recebedor_sede = request.POST.get('nome_recebedor_sede', '')
            if 'planilha_padrao_sede' in request.FILES:
                config_sede.planilha_padrao_sede = request.FILES['planilha_padrao_sede']
            config_sede.save()
            messages.success(request, "Configurações da Sede atualizadas com sucesso.")

        return redirect('tesouraria:configuracoes')

    return render(request, 'tesouraria/configuracoes.html', {
        'categorias': categorias,
        'tags': tags,
        'config_sede': config_sede
    })

@login_required
@tesouraria_required
def dar_baixa_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)

    if request.method == 'POST':
        if lancamento.status == 'pendente' or lancamento.status == 'atrasado':
            lancamento.status = 'pago'
            lancamento.data_pagamento = datetime.date.today()
            lancamento.save()

            LogImutavel.objects.create(
                membro=request.user,
                acao=f"DEU_BAIXA_LANCAMENTO_{lancamento.id}",
                dados_acao=f"Marcou como PAGO. Valor: {lancamento.valor}"
            )
            messages.success(request, 'Lançamento atualizado para PAGO com sucesso.')
        else:
            messages.warning(request, 'Este lançamento já está pago ou cancelado.')

    return redirect('tesouraria:detalhe_lancamento', pk=pk)

@csrf_exempt
@login_required
@tesouraria_required
def api_scan_comprovante(request):
    if request.method == 'POST':
        # Frontend envia como 'comprovante' via FormData
        file_obj = request.FILES.get('comprovante') or request.FILES.get('file')
        if not file_obj:
            return JsonResponse({'error': 'Nenhum arquivo enviado.'}, status=400)

        from .models import CategoriaTesouraria
        categorias = list(CategoriaTesouraria.objects.values('id', 'nome'))

        try:
            dados = analisar_comprovante_tesouraria(file_obj, categorias=categorias)
            return JsonResponse({'status': 'success', 'dados': dados})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
@tesouraria_required
def gerar_e_revisar_planilha_sede(request):
    mes = int(request.GET.get('mes', datetime.date.today().month))
    ano = int(request.GET.get('ano', datetime.date.today().year))
    try:
        caminho_planilha = gerar_planilha_sede_mensal(mes, ano)
        return FileResponse(open(caminho_planilha, 'rb'), as_attachment=True, filename=f"Relatorio_Sede_{mes:02d}_{ano}.xlsx")
    except Exception as e:
        messages.error(request, f"Erro ao gerar planilha: {str(e)}")
        return redirect('tesouraria:lista_lancamentos')

@login_required
@tesouraria_required
def enviar_relatorio_sede_email(request):
    mes = int(request.POST.get('mes', datetime.date.today().month))
    ano = int(request.POST.get('ano', datetime.date.today().year))
    config = ConfiguracaoTesouraria.objects.first()

    if not config or not config.email_sede:
        messages.error(request, "E-mail da Sede não configurado.")
        return redirect('tesouraria:lista_lancamentos')

    try:
        caminho_planilha = gerar_planilha_sede_mensal(mes, ano)

        assunto = f"Relatório Financeiro {mes:02d}/{ano} - Congregação Local"
        corpo_email = render_to_string('tesouraria/emails/relatorio_mensal_sede.html', {
            'mes': mes,
            'ano': ano,
            'nome_recebedor': config.nome_recebedor_sede
        })

        email = EmailMessage(
            assunto,
            corpo_email,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'nao-responda@igreja.com'),
            [config.email_sede]
        )
        email.content_subtype = "html"
        email.attach_file(caminho_planilha)
        email.send()

        LogImutavel.objects.create(
            membro=request.user,
            acao="ENVIO_RELATORIO_SEDE",
            dados_acao=f"Relatório de {mes}/{ano} enviado para {config.email_sede}"
        )

        messages.success(request, "Relatório enviado à Sede com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao enviar e-mail: {str(e)}")

    return redirect('tesouraria:lista_lancamentos')

# =========================================================
# Lógica de Importação em Lote com IA (Staging Area)
# =========================================================

@login_required
@tesouraria_required
def download_template_importacao(request):
    """Retorna uma planilha XLSX vazia com cabeçalhos para preenchimento."""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Template_Importacao_Tesouraria.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Importação"

    headers = [
        "Data Vencimento", "Descricao", "Tipo (entrada/saida)", "Valor",
        "Forma Pagamento", "Categoria", "Impostos",
        "Parcelado (sim/nao)", "Numero Parcelas", "Parcela Atual", "Observacoes"
    ]
    ws.append(headers)

    # Example row
    ws.append(["2025-01-10", "Compra de Cadeiras", "saida", 1500.00, "pix", "Móveis", 0, "sim", 5, 1, "Loja XYZ"])

    wb.save(response)
    return response

import json

@login_required
@tesouraria_required
def preview_importacao(request):
    """Recebe a planilha, processa via IA e armazena na sessão para revisão (Staging)."""
    if request.method == 'POST':
        if 'planilha_importacao' not in request.FILES:
            messages.error(request, "Nenhuma planilha enviada.")
            return redirect('tesouraria:lista_lancamentos')

        file_obj = request.FILES['planilha_importacao']

        from .models import CategoriaTesouraria
        categorias = list(CategoriaTesouraria.objects.values('id', 'nome'))

        try:
            # IA processa e valida o lote
            dados = analisar_planilha_importacao(file_obj, categorias)

            # Se houver erros graves, aborta
            if dados.get("erros_críticos") and len(dados["erros_críticos"]) > 0:
                for erro in dados["erros_críticos"]:
                    messages.error(request, f"Erro Crítico (IA): {erro}")
                return redirect('tesouraria:lista_lancamentos')

            # Armazena na sessão
            request.session['import_lote_tesouraria'] = dados.get("lancamentos", [])
            messages.success(request, f"IA leu {len(dados.get('lancamentos', []))} lançamentos com sucesso. Revise antes de salvar.")
            return render(request, 'tesouraria/preview_importacao.html', {'lancamentos': request.session['import_lote_tesouraria']})

        except Exception as e:
            messages.error(request, str(e))
            return redirect('tesouraria:lista_lancamentos')

    # GET: Se já tem sessão, exibe, senão redireciona
    if 'import_lote_tesouraria' in request.session:
        return render(request, 'tesouraria/preview_importacao.html', {'lancamentos': request.session['import_lote_tesouraria']})

    return redirect('tesouraria:lista_lancamentos')

@login_required
@tesouraria_required
def confirmar_importacao(request):
    """Varre a sessão e grava em lote no BD."""
    if request.method == 'POST':
        if 'import_lote_tesouraria' not in request.session:
            messages.error(request, "Sessão expirada ou nenhum dado para importar.")
            return redirect('tesouraria:lista_lancamentos')

        lancamentos_session = request.session['import_lote_tesouraria']

        from .models import CategoriaTesouraria

        count = 0
        for item in lancamentos_session:
            cat_id = item.get('categoria_id')
            categoria = CategoriaTesouraria.objects.filter(id=cat_id).first() if cat_id else None
            if not categoria:
                # Fallback genérico se a IA não mapeou e usuário não corrigiu
                categoria = CategoriaTesouraria.objects.first()

            Lancamento.objects.create(
                tipo=item.get('tipo', 'saida'),
                valor=item.get('valor', 0),
                data_vencimento=item.get('data_vencimento', datetime.date.today()),
                data_lancamento=item.get('data_lancamento') or None,
                descricao=item.get('descricao', 'Sem Descrição'),
                categoria=categoria,
                forma_pagamento=item.get('forma_pagamento', 'outros')[:20],
                impostos=item.get('impostos') or 0,
                is_parcelado=bool(item.get('is_parcelado', False)),
                numero_parcelas=item.get('numero_parcelas') or 1,
                parcela_atual=item.get('parcela_atual') or 1,
                observacoes=item.get('observacoes', ''),
                responsavel=request.user,
                status='pago' # Lote assume pago, pode ser ajustado
            )
            count += 1

        LogImutavel.objects.create(
            membro=request.user,
            acao="IMPORTACAO_LOTE_TESOURARIA",
            dados_acao=f"Importou {count} lançamentos validados pela IA."
        )

        del request.session['import_lote_tesouraria']
        messages.success(request, f"{count} lançamentos importados com sucesso militar!")
        return redirect('tesouraria:lista_lancamentos')

    return redirect('tesouraria:lista_lancamentos')
