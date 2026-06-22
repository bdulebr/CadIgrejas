"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: intranet/services/gmail_service.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
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
    from core.models import EmailLog

    if not destinatario:
        return False

    if not _is_email_active():
        str_destinatario = destinatario if isinstance(destinatario, str) else ", ".join(destinatario)[:254]
        print(f"[E-mail HTML PAUSADO - MASTER SWITCH OFF] Para: {str_destinatario} | Assunto: {assunto}")
        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto,
            status='falha',
            erro_mensagem="Envios globais pausados pelo Sysadmin."
        )
        return True # Retorna True para não quebrar a lógica das rotinas

    try:
        from core.models import ConfiguracaoSistema
        from django.template import Template, Context

        # Tenta achar o template no banco. (Ex: 'escala_cancelada.html' -> 'email_escala_cancelada')
        acao = template_name.replace('.html', '')
        identificador = f"email_{acao}"

        template_dinamico = None

        # Injeta variáveis globais como IGREJA_NOME, IGREJA_LOGO
        config_sys = ConfiguracaoSistema.objects.first()
        if config_sys:
            context['IGREJA_NOME'] = config_sys.igreja_nome
            context['IGREJA_CNPJ'] = config_sys.cnpj
            if config_sys.igreja_logo:
                context['IGREJA_LOGO'] = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000') + config_sys.igreja_logo.url

        if template_dinamico:
            if template_dinamico.titulo and template_dinamico.titulo.startswith('E-mail:'):
                assunto_real = template_dinamico.titulo.replace('E-mail: ', '')
            elif template_dinamico.titulo:
                assunto_real = template_dinamico.titulo
            else:
                assunto_real = assunto

            raw_html = f"<style>{template_dinamico.css_canva}</style>\n{template_dinamico.html_canva}"
            t = Template(raw_html)
            c = Context(context)
            html_content = t.render(c)
        else:
            assunto_real = assunto
            # Fallback para os arquivos físicos caso o template falhe
            if '/' in template_name:
                # O template_name já contém um caminho completo (ex: ministerio_casais/email.html)
                html_content = render_to_string(template_name, context)
            else:
                # O template_name é apenas o arquivo (ex: boletos.html) -> tenta na pasta emails/
                html_content = render_to_string(f"emails/{template_name}", context)

        # Versão segura de texto puro
        text_content = strip_tags(html_content)

        lista_destinatarios = destinatario if isinstance(destinatario, list) else [destinatario]
        msg = EmailMultiAlternatives(
            subject=assunto_real,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=lista_destinatarios
        )
        msg.attach_alternative(html_content, "text/html")

        # Anexar arquivos, se houver: anexos=[('nome.pdf', conteudo_bytes, 'application/pdf')]
        if anexos:
            for nome_arquivo, conteudo, mimetype in anexos:
                msg.attach(nome_arquivo, conteudo, mimetype)

        # DISPARO REAL
        # DISPARO REAL
        msg.send()

        str_destinatario = destinatario if isinstance(destinatario, list) else ", ".join(destinatario)[:254]
        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto_real,
            status='enviado',
            corpo_html=html_content
        )

        print(f"[E-mail HTML Real Enviado] Para: {str_destinatario} | Assunto: {assunto_real}")
        return True
    except Exception as e:
        print(f"[FALHA E-MAIL REAL] Você configurou a Senha de Aplicativo no settings.py? Erro: {str(e)}")
        str_destinatario = destinatario if isinstance(destinatario, list) else destinatario
        if isinstance(str_destinatario, list): str_destinatario = ", ".join(str_destinatario)[:254]
        # Tentamos salvar o html_content, se ele não falhou antes de gerá-lo
        try:
            corpo = html_content
        except NameError:
            corpo = "Falha antes da geração do HTML"

        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto,
            status='falha',
            erro_mensagem=str(e),
            corpo_html=corpo
        )
        return False

def reenviar_email_falho(log_id):
    """
    Tenta reenviar um e-mail que falhou, recuperando seu corpo HTML.
    """
    from core.models import EmailLog
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags
    from django.conf import settings

    try:
        log = EmailLog.objects.get(id=log_id, status='falha')
    except EmailLog.DoesNotExist:
        return False, "Log não encontrado ou já enviado."

    if not _is_email_active():
        return False, "Envios globais estão pausados pelo SysAdmin."

    if not log.corpo_html:
        return False, "O corpo HTML não foi salvo para este e-mail. Não é possível reenviar."

    log.qtd_reenvios += 1
    log.save()

    try:
        text_content = strip_tags(log.corpo_html)
        lista_destinatarios = [x.strip() for x in log.destinatario.split(",")]

        msg = EmailMultiAlternatives(
            subject=log.assunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=lista_destinatarios
        )
        msg.attach_alternative(log.corpo_html, "text/html")
        msg.send()

        log.status = 'enviado'
        log.erro_mensagem = None
        log.save()
        return True, "E-mail reenviado com sucesso!"
    except Exception as e:
        log.erro_mensagem = str(e)
        log.save()
        return False, f"Falha no reenvio: {str(e)}"

def enviar_email_simples(destinatario, assunto, corpo, anexos=None):
    """
    Fallback para e-mails legados/simples sem template.
    Agora envia o e-mail DE VERDADE em vez de só printar e suporta anexos.
    """
    from core.models import EmailLog

    if not destinatario:
        return False

    str_destinatario = destinatario if isinstance(destinatario, str) else ", ".join(destinatario)[:254]
    if not _is_email_active():
        print(f"[E-mail Simples PAUSADO - MASTER SWITCH OFF] Para: {str_destinatario}")
        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto,
            status='falha',
            erro_mensagem="Envios globais pausados pelo Sysadmin."
        )
        return True

    try:
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives

        lista_destinatarios = destinatario if isinstance(destinatario, list) else [destinatario]
        msg = EmailMultiAlternatives(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=lista_destinatarios
        )

        if anexos:
            for nome_arquivo, conteudo, mimetype in anexos:
                msg.attach(nome_arquivo, conteudo, mimetype)

        msg.send()
        str_destinatario = destinatario if isinstance(destinatario, str) else ", ".join(destinatario)[:254]
        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto,
            status='enviado'
        )
        print(f"[E-mail Simples Real Enviado] Para: {destinatario}")
        return True
    except Exception as e:
        print(f"[FALHA] Sem SMTP: {str(e)}")
        str_destinatario = destinatario if isinstance(destinatario, str) else ", ".join(destinatario)[:254]
        EmailLog.objects.create(
            destinatario=str_destinatario,
            assunto=assunto,
            status='falha',
            erro_mensagem=str(e)
        )
        return False
