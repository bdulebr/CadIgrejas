from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def _is_email_active():
    from core.models import ConfiguracaoSistema
    config = ConfiguracaoSistema.objects.first()
    return config.envios_email_ativos if config else True

def enviar_email_html(destinatario, assunto, template_name, context, anexos=None):
    """
    Função oficial de disparo de e-mails usando Django SMTP com templates HTML.
    O FIM DOS MOCKS!
    """
    if not destinatario:
        return False
        
    if not _is_email_active():
        print(f"[E-mail HTML PAUSADO - MASTER SWITCH OFF] Para: {destinatario} | Assunto: {assunto}")
        return True # Retorna True para não quebrar a lógica das rotinas
        
    try:
        from core.models import TemplateDocumento
        from django.template import Template, Context
        
        # Tenta achar um template customizado no banco. (Ex: 'escala_cancelada.html' -> 'escala_cancelada')
        acao = template_name.replace('.html', '')
        template_dinamico = TemplateDocumento.objects.filter(nome_acao=acao, tipo='email', ativo=True).first()
        
        if template_dinamico:
            if template_dinamico.assunto_padrao:
                assunto = template_dinamico.assunto_padrao
            
            # GrapesJS costuma ter CSS e HTML separados
            raw_html = f"<style>{template_dinamico.css_content}</style>\n{template_dinamico.html_content}"
            t = Template(raw_html)
            c = Context(context)
            html_content = t.render(c)
        else:
            # Fallback para os arquivos físicos
            html_content = render_to_string(f"emails/{template_name}", context)
            
        # Versão segura de texto puro
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=assunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Anexar arquivos, se houver: anexos=[('nome.pdf', conteudo_bytes, 'application/pdf')]
        if anexos:
            for nome_arquivo, conteudo, mimetype in anexos:
                msg.attach(nome_arquivo, conteudo, mimetype)
        
        # DISPARO REAL
        msg.send()
        
        print(f"[E-mail HTML Real Enviado] Para: {destinatario} | Assunto: {assunto}")
        return True
    except Exception as e:
        print(f"[FALHA E-MAIL REAL] Você configurou a Senha de Aplicativo no settings.py? Erro: {str(e)}")
        return False

def enviar_email_simples(destinatario, assunto, corpo):
    """
    Fallback para e-mails legados/simples sem template.
    Agora envia o e-mail DE VERDADE em vez de só printar.
    """
    if not destinatario:
        return False
        
    if not _is_email_active():
        print(f"[E-mail Simples PAUSADO - MASTER SWITCH OFF] Para: {destinatario}")
        return True
        
    try:
        msg = EmailMultiAlternatives(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )
        msg.send()
        print(f"[E-mail Simples Real Enviado] Para: {destinatario}")
        return True
    except Exception as e:
        print(f"[FALHA] Sem SMTP: {str(e)}")
        return False
