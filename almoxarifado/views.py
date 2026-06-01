"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: almoxarifado/views.py
* DESCRIÇÃO: Views do módulo de inventário e empréstimos
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 25/05/2026 14:05
* LOG DE ALTERAÇÕES:
* - 25/05/2026 14:05: Criação inicial das rotas
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Ativo, Emprestimo, AlimentoLote, Manutencao
from core.models import Membro, LogAuditoria
from gestao_membros.models import Departamento
import json

def criar_log_imutavel(usuario, acao, tabela, dados):
    """
    Motor interno do Zero-Trust. Gera o hash chain.
    """
    LogAuditoria.objects.create(
        usuario_acao=usuario,
        acao_realizada=acao,
        tabela_afetada=tabela,
        diferenca_json=dados
    )

def is_lider(user):
    return user.nivel_hierarquico in ['super_admin', 'pastor_regente', 'pastor', 'missionario', 'lider', 'sub_lider']

def can_edit_almoxarifado(user):
    return user.nivel_hierarquico == 'super_admin' or user.is_superuser or user.departamentos_liderados.filter(nome__icontains='Almoxarifado').exists()

@login_required
def painel_inventario(request):
    busca_codigo = request.GET.get('busca_codigo')
    if busca_codigo:
        ativo_qr = Ativo.objects.filter(codigo_patrimonio=busca_codigo).first()
        if ativo_qr:
            return redirect('ativo_detalhe', ativo_id=ativo_qr.id)
        else:
            messages.error(request, f'Ativo com código {busca_codigo} não encontrado no banco de dados.')
            return redirect('painel_inventario')

    departamentos = Departamento.objects.all()

    ativos = Ativo.objects.filter(departamento_dono__in=departamentos).order_by('-id')
    from django.db.models import Q
    membros = Membro.objects.filter(
        Q(is_active=True) & (
            Q(departamentos_ativos__in=departamentos) |
            Q(departamentos_liderados__in=departamentos) |
            Q(departamentos_subliderados__in=departamentos) |
            Q(nivel_hierarquico__in=['super_admin', 'pastor_regente', 'pastor'])
        )
    ).distinct()

    # Estatísticas do Dashboard
    stats = {
        'total': ativos.count(),
        'emprestados': ativos.filter(status='emprestado').count(),
        'danificados': ativos.filter(status='quebrado').count(),
        'manutencao': ativos.filter(status='manutencao').count(),
    }

    return render(request, 'almoxarifado/inventario.html', {
        'ativos': ativos,
        'departamentos': departamentos,
        'membros': membros,
        'stats': stats
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def registrar_novo_ativo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        codigo = request.POST.get('codigo_patrimonio')
        categoria = request.POST.get('categoria')
        dept_id = request.POST.get('departamento_id')

        origem = request.POST.get('origem', 'desconhecido')
        fornecedor_doador = request.POST.get('fornecedor_doador', '')
        valor = request.POST.get('valor', 0.00)

        if not valor:
            valor = 0.00

        foto_item = request.FILES.get('foto_item')
        anexo_comprovante = request.FILES.get('anexo_comprovante')
        localizacao = request.POST.get('localizacao', '')
        data_aquisicao = request.POST.get('data_aquisicao') or None

        try:
            novo_ativo = Ativo.objects.create(
                localizacao=localizacao,
                data_aquisicao=data_aquisicao,
                nome=nome,
                codigo_patrimonio=codigo,
                categoria=categoria,
                departamento_dono_id=dept_id,
                origem=origem,
                fornecedor_doador=fornecedor_doador,
                valor=valor,
                foto_item=foto_item,
                anexo_comprovante=anexo_comprovante
            )

            # Auditoria Imutável Zero-Trust
            criar_log_imutavel(
                usuario=request.user,
                acao='CRIAR_ATIVO',
                tabela='almoxarifado_ativo',
                dados={'id': novo_ativo.id, 'nome': nome, 'codigo': codigo, 'origem': origem, 'valor': str(valor)}
            )

            messages.success(request, f'Equipamento {nome} registrado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao registrar ativo (Código já existe?): {str(e)}')

    return redirect('painel_inventario')

@login_required
@user_passes_test(can_edit_almoxarifado)
def registrar_emprestimo(request):
    if request.method == 'POST':
        ativo_id = request.POST.get('ativo_id')
        membro_id = request.POST.get('membro_id')
        data_prevista = request.POST.get('data_prevista')
        obs = request.POST.get('observacao', '')

        ativo = get_object_or_404(Ativo, id=ativo_id)

        if ativo.status != 'disponivel':
            messages.error(request, 'Este ativo não está disponível para empréstimo!')
            return redirect('painel_inventario')

        novo_emprestimo = Emprestimo.objects.create(
            ativo_id=ativo_id,
            membro_solicitante_id=membro_id,
            data_devolucao_prevista=data_prevista,
            observacao=obs
        )

        # Trava o ativo
        ativo.status = 'emprestado'
        ativo.save()

        # Auditoria Imutável Zero-Trust
        criar_log_imutavel(
            usuario=request.user,
            acao='REGISTRAR_EMPRESTIMO',
            tabela='almoxarifado_emprestimo',
            dados={
                'emprestimo_id': novo_emprestimo.id,
                'ativo': ativo.nome,
                'solicitante_id': membro_id,
                'data_prevista': data_prevista
            }
        )

        messages.success(request, 'Empréstimo registrado com sucesso.')

    return redirect('painel_inventario')

@login_required
@user_passes_test(can_edit_almoxarifado)
def devolver_item(request, ativo_id):
    if request.method == 'POST':
        ativo = get_object_or_404(Ativo, id=ativo_id)
        novo_status = request.POST.get('novo_status', 'disponivel')

        # Encontrar o empréstimo em aberto
        emprestimo = ativo.historico_emprestimos.filter(data_devolucao_real__isnull=True).last()
        if emprestimo:
            emprestimo.data_devolucao_real = timezone.now()
            emprestimo.save()

        ativo.status = novo_status
        ativo.save()

        # Auditoria Imutável Zero-Trust
        criar_log_imutavel(
            usuario=request.user,
            acao='DEVOLVER_ATIVO',
            tabela='almoxarifado_ativo',
            dados={
                'ativo_id': ativo.id,
                'ativo_nome': ativo.nome,
                'novo_status': novo_status,
                'emprestimo_encerrado': emprestimo.id if emprestimo else None
            }
        )

        messages.success(request, 'Devolução registrada no sistema e auditada.')

    return redirect('painel_inventario')

@login_required
def ativo_detalhe(request, ativo_id):
    ativo = get_object_or_404(Ativo, id=ativo_id)

    historico_emprestimos = ativo.historico_emprestimos.all().order_by('-data_retirada')
    historico_manutencoes = ativo.historico_manutencoes.all().order_by('-data_envio')

    return render(request, 'almoxarifado/ativo_detalhe.html', {
        'ativo': ativo,
        'historico_emprestimos': historico_emprestimos,
        'historico_manutencoes': historico_manutencoes
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def deletar_ativo(request, ativo_id):
    # ... código mantido, só vou inserir no final

    if request.method == 'POST':
        messages.error(request, 'Blindagem Zero-Trust: Itens de Patrimônio não podem ser excluídos. Altere o status para "Baixado/Quebrado" para manter o histórico.')

    return redirect('painel_inventario')

@login_required
@user_passes_test(can_edit_almoxarifado)
def enviar_manutencao(request, ativo_id):
    if request.method == 'POST':
        ativo = get_object_or_404(Ativo, id=ativo_id)
        oficina = request.POST.get('oficina_tecnico')
        problema = request.POST.get('descricao_problema')

        ativo.status = 'manutencao'
        ativo.save()

        manutencao = ativo.historico_manutencoes.create(
            oficina_tecnico=oficina,
            descricao_problema=problema
        )

        criar_log_imutavel(
            usuario=request.user,
            acao='ENVIAR_MANUTENCAO',
            tabela='almoxarifado_manutencao',
            dados={'ativo_id': ativo.id, 'manutencao_id': manutencao.id, 'oficina': oficina}
        )
        messages.success(request, 'Equipamento enviado para manutenção.')
    return redirect('ativo_detalhe', ativo_id=ativo_id)

@login_required
@user_passes_test(can_edit_almoxarifado)
def concluir_manutencao(request, manutencao_id):
    if request.method == 'POST':
        man = get_object_or_404(Manutencao, id=manutencao_id)

        custo = request.POST.get('custo', 0)
        solucao = request.POST.get('solucao_aplicada', '')

        man.custo = custo
        man.solucao_aplicada = solucao
        man.data_retorno_real = timezone.now()
        man.save()

        # Voltar o ativo para disponível (a menos que a solução tenha sido "Lixo")
        ativo = man.ativo
        ativo.status = 'disponivel'
        ativo.save()

        criar_log_imutavel(
            usuario=request.user,
            acao='CONCLUIR_MANUTENCAO',
            tabela='almoxarifado_manutencao',
            dados={'manutencao_id': man.id, 'ativo_id': ativo.id, 'custo': custo}
        )
        messages.success(request, f'Manutenção de {ativo.nome} concluída! Ativo de volta ao estoque.')

    return redirect('ativo_detalhe', ativo_id=man.ativo.id)

@login_required
@user_passes_test(can_edit_almoxarifado)
def alocar_uso_fixo(request, ativo_id):
    if request.method == 'POST':
        ativo = get_object_or_404(Ativo, id=ativo_id)
        localizacao = request.POST.get('localizacao', '').strip()

        if not localizacao:
            messages.error(request, 'Você deve informar a localização da sala/ambiente.')
            return redirect('ativo_detalhe', ativo_id=ativo.id)

        ativo.status = 'em_uso_fixo'
        ativo.localizacao = localizacao
        ativo.save()

        criar_log_imutavel(
            usuario=request.user,
            acao='ALOCAR_FIXO',
            tabela='almoxarifado_ativo',
            dados={'ativo_id': ativo.id, 'localizacao': localizacao}
        )
        messages.success(request, f'O item {ativo.nome} foi alocado em Uso Fixo na sala: {localizacao}.')
    return redirect('ativo_detalhe', ativo_id=ativo.id)

@login_required
@user_passes_test(can_edit_almoxarifado)
def remover_uso_fixo(request, ativo_id):
    if request.method == 'POST':
        ativo = get_object_or_404(Ativo, id=ativo_id)
        local_antigo = ativo.localizacao
        ativo.status = 'disponivel'
        ativo.localizacao = ''
        ativo.save()

        criar_log_imutavel(
            usuario=request.user,
            acao='REMOVER_FIXO',
            tabela='almoxarifado_ativo',
            dados={'ativo_id': ativo.id, 'local_antigo': local_antigo}
        )
        messages.success(request, f'O item {ativo.nome} retornou para o Almoxarifado.')
    return redirect('ativo_detalhe', ativo_id=ativo.id)

@login_required
def gerar_termo_pdf(request, ativo_id):
    ativo = get_object_or_404(Ativo, id=ativo_id)
    emprestimo = ativo.historico_emprestimos.filter(data_devolucao_real__isnull=True).last()

    if not emprestimo:
        messages.error(request, 'Não há empréstimo em aberto para este item.')
        return redirect('painel_inventario')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="termo_{ativo.codigo_patrimonio}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#b91c1c"), # Red warning
        spaceAfter=30,
        alignment=1
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18,
        spaceAfter=15,
        alignment=4 # Justify
    )

    elements.append(Paragraph("TERMO DE RESPONSABILIDADE FÍSICA", title_style))

    texto = f"""
    Eu, <b>{emprestimo.membro_solicitante.get_full_name()}</b>, portador(a) do CPF {emprestimo.membro_solicitante.cpf or 'Não informado'},
    voluntário(a) ativo(a) da Palavra de Vida Enseada, declaro ter recebido sob minha responsabilidade, em perfeito estado de conservação e funcionamento
    (salvo as observações abaixo), o equipamento pertencente ao patrimônio da instituição, discriminado a seguir:
    """
    elements.append(Paragraph(texto, body_style))

    detalhes = f"""
    <b>Equipamento:</b> {ativo.nome}<br/>
    <b>Código de Patrimônio/Serial:</b> {ativo.codigo_patrimonio}<br/>
    <b>Departamento Proprietário:</b> {ativo.departamento_dono.nome}<br/>
    <b>Data de Retirada:</b> {emprestimo.data_retirada.strftime('%d/%m/%Y às %H:%M')}<br/>
    <b>Data de Devolução Prevista:</b> {emprestimo.data_devolucao_prevista.strftime('%d/%m/%Y')}<br/>
    <b>Observações Adicionais:</b> {emprestimo.observacao or 'Nenhuma'}<br/>
    """
    elements.append(Paragraph(detalhes, body_style))

    compromisso = """
    Comprometo-me a zelar pela integridade do referido bem, responsabilizando-me por qualquer dano, perda ou extravio
    decorrente de negligência, mau uso ou imperícia. Estou ciente de que, caso ocorra qualquer eventualidade com o equipamento
    sob minha guarda, assumo o compromisso legal e moral de providenciar o conserto ou reposição integral do valor do bem.
    <br/><br/>
    O uso deste equipamento destina-se exclusivamente às atividades autorizadas pelo departamento da Palavra de Vida Enseada.
    """
    elements.append(Paragraph(compromisso, body_style))

    elements.append(Spacer(1, 60))

    assinatura = f"""
    ___________________________________________________<br/>
    {emprestimo.membro_solicitante.get_full_name()}<br/>
    Data: ____/____/________
    """

    elements.append(Paragraph(assinatura, ParagraphStyle(name='Center', parent=body_style, alignment=1)))

    doc.build(elements)

    # Zero-Trust Audit
    criar_log_imutavel(
        usuario=request.user,
        acao='GEROU_TERMO_PDF',
        tabela='almoxarifado_emprestimo',
        dados={'emprestimo_id': emprestimo.id, 'ativo': ativo.nome}
    )

    return response

@login_required
def painel_alimentos(request):
    departamentos = Departamento.objects.all()

    lotes = AlimentoLote.objects.filter(departamento__in=departamentos).order_by('data_vencimento')

    return render(request, 'almoxarifado/alimentos.html', {
        'lotes': lotes,
        'departamentos': departamentos
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def adicionar_alimento(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        quantidade = request.POST.get('quantidade')
        data_vencimento = request.POST.get('data_vencimento')
        departamento_id = request.POST.get('departamento_id')
        obs = request.POST.get('observacoes', '')
        anexo = request.FILES.get('anexo_nota_fiscal')

        try:
            novo_lote = AlimentoLote.objects.create(
                nome=nome,
                quantidade_inicial=quantidade,
                quantidade_atual=quantidade,
                data_vencimento=data_vencimento,
                departamento_id=departamento_id,
                observacoes=obs,
                anexo_nota_fiscal=anexo
            )

            # Auditoria Imutável Zero-Trust
            criar_log_imutavel(
                usuario=request.user,
                acao='CRIAR_ALIMENTO',
                tabela='almoxarifado_alimentolote',
                dados={'lote_id': novo_lote.id, 'nome': nome, 'qtd': quantidade, 'vence': data_vencimento}
            )

            messages.success(request, f'Lote de {nome} adicionado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar alimento: {str(e)}')

    return redirect('painel_alimentos')

@login_required
@user_passes_test(can_edit_almoxarifado)
def deletar_alimento(request, lote_id):
    if request.method == 'POST':
        messages.error(request, 'Blindagem Zero-Trust: Lotes de Alimentos não podem ser excluídos do sistema. Registre uma "Saída" (consumo/descarte) para manter a rastreabilidade logística.')
    return redirect('painel_alimentos')

@login_required
def alimento_detalhe(request, lote_id):
    lote = get_object_or_404(AlimentoLote, id=lote_id)

    transacoes = lote.transacoes.all().order_by('-data_transacao')

    return render(request, 'almoxarifado/alimento_detalhe.html', {
        'lote': lote,
        'transacoes': transacoes
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def transacionar_alimento(request, lote_id):
    if request.method == 'POST':
        lote = get_object_or_404(AlimentoLote, id=lote_id)

        tipo = request.POST.get('tipo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino_origem = request.POST.get('destino_origem')
        observacao = request.POST.get('observacao', '')
        anexo = request.FILES.get('anexo_comprovante')

        if tipo == 'saida' and quantidade > lote.quantidade_atual:
            messages.error(request, f'Erro: Você está tentando dar saída de {quantidade} unidades, mas o estoque tem apenas {lote.quantidade_atual}.')
            return redirect('alimento_detalhe', lote_id=lote_id)

        from .models import TransacaoAlimento

        # Cria a transação
        transacao = TransacaoAlimento.objects.create(
            lote=lote,
            tipo=tipo,
            quantidade=quantidade,
            destino_origem=destino_origem,
            observacao=observacao,
            anexo_comprovante=anexo,
            membro_responsavel=request.user
        )

        # Atualiza o saldo do Lote
        if tipo == 'saida':
            lote.quantidade_atual -= quantidade
        else:
            lote.quantidade_atual += quantidade

        lote.save()

        # Hash Chain
        criar_log_imutavel(
            usuario=request.user,
            acao='TRANSACAO_ESTOQUE_ALIMENTO',
            tabela='almoxarifado_transacaoalimento',
            dados={
                'transacao_id': transacao.id,
                'lote_id': lote.id,
                'tipo': tipo,
                'qtd': quantidade,
                'saldo_final': lote.quantidade_atual
            }
        )


        messages.success(request, f'Transação registrada! Novo saldo do lote: {lote.quantidade_atual} un.')

    return redirect('alimento_detalhe', lote_id=lote_id)

@login_required
def scanner_qr(request):
    return render(request, 'almoxarifado/scanner_qr.html')

def pegar_item_almoxarifado(request):
    modo = request.GET.get('modo', 'manual')
    if request.method == 'POST':
        codigo = request.POST.get('codigo_patrimonio')
        membro_id = request.POST.get('membro_id')
        tipo_retirada = request.POST.get('tipo_retirada')
        data_devolucao = request.POST.get('data_devolucao')
        localizacao = request.POST.get('localizacao')
        observacao = request.POST.get('observacao')

        ativo = Ativo.objects.filter(codigo_patrimonio=codigo).first()
        if not ativo:
            messages.error(request, 'Ativo não encontrado ou código inválido!')
            return redirect(f'/almoxarifado/pegar-item/?modo={modo}')

        if ativo.status != 'disponivel':
            messages.error(request, f'O item {ativo.nome} não está disponível no momento (Status: {ativo.get_status_display()}).')
            return redirect(f'/almoxarifado/pegar-item/?modo={modo}')

        membro = get_object_or_404(Membro, id=membro_id)

        if tipo_retirada == 'temporario':
            if not data_devolucao:
                messages.error(request, 'Data de devolução é obrigatória para retiradas temporárias.')
                return redirect(f'/almoxarifado/pegar-item/?modo={modo}')

            Emprestimo.objects.create(
                ativo=ativo,
                membro_solicitante=membro,
                data_devolucao_prevista=data_devolucao,
                observacao=observacao
            )
            ativo.status = 'emprestado'
            ativo.save()
            criar_log_imutavel(membro, 'RETIRADA_TEMPORARIA_SELF_SERVICE', 'almoxarifado_ativo', json.dumps({"ativo_id": ativo.id, "novo_status": "emprestado", "obs": observacao}))
            messages.success(request, f'Item {ativo.nome} emprestado com sucesso para {membro.first_name}!')

        elif tipo_retirada == 'permanente':
            if not localizacao:
                messages.error(request, 'Localização de destino é obrigatória para itens de uso fixo.')
                return redirect(f'/almoxarifado/pegar-item/?modo={modo}')

            ativo.status = 'em_uso_fixo'
            ativo.localizacao = localizacao
            ativo.save()
            criar_log_imutavel(membro, 'RETIRADA_PERMANENTE_SELF_SERVICE', 'almoxarifado_ativo', json.dumps({"ativo_id": ativo.id, "novo_status": "em_uso_fixo", "local": localizacao, "obs": observacao}))
            messages.success(request, f'Item {ativo.nome} alocado em {localizacao} com sucesso!')

        return redirect('login')

    membros = Membro.objects.filter(is_active=True).order_by('first_name')
    return render(request, 'almoxarifado/pegar_item_self_service.html', {
        'modo': modo,
        'membros': membros
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def livro_caixa_almoxarifado(request):
    logs = LogAuditoria.objects.filter(tabela_afetada__startswith='almoxarifado').order_by('-data_hora')
    emprestimos = Emprestimo.objects.order_by('-data_retirada')
    return render(request, 'almoxarifado/livro_caixa.html', {
        'logs': logs,
        'emprestimos': emprestimos
    })

@login_required
@user_passes_test(can_edit_almoxarifado)
def ai_insights_almoxarifado(request):
    try:
        from intranet.services.groq_ai import obter_client_groq
        client = obter_client_groq()
        if not client:
            return HttpResponse('<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro: Chave do Groq não configurada.</div>')

        # Coletar estatísticas do almoxarifado
        from .models import Ativo, Emprestimo, AlimentoLote
        from django.db.models import Sum
        from django.utils import timezone

        total_ativos = Ativo.objects.count()
        valor_total = Ativo.objects.aggregate(total=Sum('valor'))['total'] or 0
        ativos_quebrados = Ativo.objects.filter(status='quebrado').count()
        ativos_manutencao = Ativo.objects.filter(status='manutencao').count()

        hoje = timezone.now().date()
        emprestimos_atrasados = Emprestimo.objects.filter(data_devolucao_prevista__lt=hoje, data_devolucao_real__isnull=True).count()
        alimentos_vencidos = AlimentoLote.objects.filter(data_vencimento__lt=hoje).exclude(status__in=['Vencido', 'Consumido']).count()
        alimentos_vencendo_breve = AlimentoLote.objects.filter(data_vencimento__gte=hoje, data_vencimento__lte=hoje + timezone.timedelta(days=15)).count()

        import json
        context_data = {
            'total_ativos_cadastrados': total_ativos,
            'valor_total_estimado': float(valor_total),
            'itens_quebrados': ativos_quebrados,
            'itens_em_manutencao': ativos_manutencao,
            'emprestimos_atrasados': emprestimos_atrasados,
            'lotes_alimentos_vencidos': alimentos_vencidos,
            'lotes_alimentos_vencendo_15_dias': alimentos_vencendo_breve
        }

        prompt = f"""
        Você é um Consultor Sênior de Logística e Almoxarifado da Igreja.
        Analise o resumo do estoque abaixo e retorne um pequeno relatório de insights em HTML (sem usar tags de Markdown como ```html).
        Use classes do TailwindCSS (como text-blue-400, font-bold, mb-2, p-4, bg-gray-800, rounded-lg) para formatar a resposta.
        Dê 3 dicas acionáveis para o líder do almoxarifado com base nestes números:

        {json.dumps(context_data)}
        """

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7
        )

        html_response = response.choices[0].message.content.replace('```html', '').replace('```', '')
        return HttpResponse(html_response)

    except Exception as e:
        return HttpResponse(f'<div class="p-4 bg-red-900/50 text-red-200 rounded-lg">Erro ao conectar com a LPU Groq: {str(e)}</div>')
