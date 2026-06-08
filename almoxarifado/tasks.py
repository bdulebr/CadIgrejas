import threading
from django.utils import timezone
from .models import MovimentacaoAlmoxarifado
from core.models import NotificacaoGlobal

def processar_pos_carrinho_background(movimentacoes_ids):
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings
    
    movs = MovimentacaoAlmoxarifado.objects.filter(id__in=movimentacoes_ids)
    if not movs.exists(): return
    
    # Notificar Líderes
    from .views import get_lideres_almoxarifado
    lideres = get_lideres_almoxarifado()
    
    primeira_mov = movs.first()
    tipo = primeira_mov.tipo
    acao = "RETIRADA (CARRINHO)" if tipo == 'retirada' else "DEVOLUÇÃO (CARRINHO)"
    
    # Resumo
    itens_pendentes = movs.filter(status_aprovacao='pendente').count()
    itens_aprovados = movs.filter(status_aprovacao='aprovado').count()
    
    resumo_msg = f"{primeira_mov.nome_digitado} processou {movs.count()} item(ns) via auto-atendimento."
    if itens_pendentes > 0:
        resumo_msg += f" ATENÇÃO: {itens_pendentes} item(ns) requerem sua aprovação no Painel."
        
    for lider in lideres:
        NotificacaoGlobal.objects.create(
            usuario=lider,
            titulo=f"Novo Lote: {acao}",
            mensagem=resumo_msg,
            icone='shopping-cart',
            cor='blue',
            link='/almoxarifado/painel/aprovacoes/'
        )
        
    # PDF LGPD Termo de Cautela
    # Só gera PDF agora para os que já estão aprovados E são permanentes/exigem cautela
    # Para simplificar: se informou e-mail e tem aprovados, gera o PDF dos aprovados.
    
    movs_aprovados = movs.filter(status_aprovacao='aprovado')
    if movs_aprovados.exists() and primeira_mov.email_digitado:
        gerar_e_enviar_pdf_termo(movs_aprovados, primeira_mov.email_digitado, primeira_mov.nome_digitado)

def gerar_e_enviar_pdf_termo(movimentacoes, email_destino, nome_usuario):
    from xhtml2pdf import pisa
    from io import BytesIO
    from django.template.loader import render_to_string
    from django.core.mail import EmailMessage
    from django.conf import settings
    
    html_str = render_to_string('almoxarifado/termo_cautela_pdf.html', {
        'movimentacoes': movimentacoes,
        'nome_usuario': nome_usuario,
        'data': timezone.now()
    })
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    
    if not pdf.err:
        email = EmailMessage(
            subject='Termo de Responsabilidade - Almoxarifado PVE',
            body=f'Olá {nome_usuario},\n\nSegue em anexo o seu Termo de Responsabilidade (LGPD) referente aos itens retirados/devolvidos no Almoxarifado.\n\nPor favor, guarde este documento.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destino],
        )
        email.attach('Termo_de_Responsabilidade_PVE.pdf', result.getvalue(), 'application/pdf')
        try:
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Erro ao enviar email PDF: {e}")
