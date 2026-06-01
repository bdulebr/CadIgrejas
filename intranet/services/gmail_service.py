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
        from midia_lgpd.models import DocumentoTemplate
        from core.models import ConfiguracaoSistema
        from django.template import Template, Context
        
        # Tenta achar o template no banco. (Ex: 'escala_cancelada.html' -> 'email_escala_cancelada')
        acao = template_name.replace('.html', '')
        identificador = f"email_{acao}"
        
        template_dinamico = DocumentoTemplate.objects.filter(identificador_sistema=identificador, ativo=True).first()
        
        # Injeta variáveis globais como IGREJA_NOME, IGREJA_LOGO
        config_sys = ConfiguracaoSistema.objects.first()
        if config_sys:
            context['IGREJA_NOME'] = config_sys.igreja_nome
            context['IGREJA_CNPJ'] = config_sys.cnpj
            if config_sys.logo:
                context['IGREJA_LOGO'] = settings.BASE_URL + config_sys.logo.url
        
        if template_dinamico:
            if template_dinamico.titulo and template_dinamico.titulo.startswith('E-mail:'):
                assunto = template_dinamico.titulo.replace('E-mail: ', '')
            elif template_dinamico.titulo:
                assunto = template_dinamico.titulo
            
            raw_html = f"<style>{template_dinamico.css_canva}</style>\n{template_dinamico.html_canva}"
            t = Template(raw_html)
            c = Context(context)
            html_content = t.render(c)
        else:
            # Fallback para os arquivos físicos caso o template falhe
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
