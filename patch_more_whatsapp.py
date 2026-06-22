import os
import re

def create_template(filename, content):
    path = os.path.join('core', 'templates', 'whatsapp', filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

create_template('casais_lembrete_curso.txt', "Lembrete: O curso {{ curso.nome }} terá aula em breve!\nAcesse a plataforma para detalhes.")
create_template('casais_nova_mensagem.txt', "Olá! Há uma nova atualização sobre o Ministério de Casais.\nAcesse a intranet para ver.")
create_template('lgpd_assinatura_pendente.txt', "Olá {{ nome }}. O seu termo LGPD está aguardando assinatura.\nAcesse o link para assinar: {{ link_assinatura }}")
create_template('lgpd_segunda_via.txt', "Olá {{ nome }}. Segue o comprovante de assinatura do termo LGPD.\nAcesse a plataforma para baixar o PDF.")

def patch_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if "enviar_whatsapp_template" not in content and "from intranet.services.gmail_service import enviar_email_html" in content:
        content = content.replace("from intranet.services.gmail_service import enviar_email_html",
                                  "from intranet.services.gmail_service import enviar_email_html\nfrom intranet.services.whatsapp_service import enviar_whatsapp_template")

    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: {old[:30]}... not found in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. ministerio_casais/signals.py
patch_file("ministerio_casais/signals.py", [
    ("""                enviar_email_html(
                    destinatario=dest,
                    assunto=assunto,
                    template_name=template_name,
                    context=contexto_email
                )""", """                enviar_email_html(
                    destinatario=dest,
                    assunto=assunto,
                    template_name=template_name,
                    context=contexto_email
                )
            # Send WhatsApp
            t1 = casal.telefone_1
            t2 = casal.telefone_2
            if t1: enviar_whatsapp_template(t1, 'casais_nova_mensagem.txt', contexto_email)
            if t2 and t2 != t1: enviar_whatsapp_template(t2, 'casais_nova_mensagem.txt', contexto_email)""")
])

# 2. ministerio_casais/management/commands/disparar_lembretes_cursos.py
patch_file("ministerio_casais/management/commands/disparar_lembretes_cursos.py", [
    ("""                        enviar_email_html(email, assunto, 'ministerio_casais/email_lembrete_curso.html', contexto)""", """                        enviar_email_html(email, assunto, 'ministerio_casais/email_lembrete_curso.html', contexto)
                        t1 = matricula.casal.telefone_1
                        t2 = matricula.casal.telefone_2
                        if t1: enviar_whatsapp_template(t1, 'casais_lembrete_curso.txt', contexto)
                        if t2 and t2 != t1: enviar_whatsapp_template(t2, 'casais_lembrete_curso.txt', contexto)""")
])

# 3. core/management/commands/enviar_lembretes_curso.py
patch_file("core/management/commands/enviar_lembretes_curso.py", [
    ("""                        enviar_email_html(
                            destinatario=email,
                            assunto=assunto,
                            template_name='ministerio_casais/email_lembrete_curso.html',
                            context=contexto
                        )""", """                        enviar_email_html(
                            destinatario=email,
                            assunto=assunto,
                            template_name='ministerio_casais/email_lembrete_curso.html',
                            context=contexto
                        )
                        t1 = matricula.casal.telefone_1
                        t2 = matricula.casal.telefone_2
                        if t1: enviar_whatsapp_template(t1, 'casais_lembrete_curso.txt', contexto)
                        if t2 and t2 != t1: enviar_whatsapp_template(t2, 'casais_lembrete_curso.txt', contexto)""")
])

# 4. midia_lgpd/views.py
patch_file("midia_lgpd/views.py", [
    ("""            enviar_email_html(
                destinatario=termo.email,
                assunto='Assinatura Pendente - Termo LGPD',
                template_name='midia_lgpd/email_assinatura_pendente.html',
                context={'termo': termo, 'link_assinatura': link_assinatura}
            )""", """            enviar_email_html(
                destinatario=termo.email,
                assunto='Assinatura Pendente - Termo LGPD',
                template_name='midia_lgpd/email_assinatura_pendente.html',
                context={'termo': termo, 'link_assinatura': link_assinatura}
            )
            if termo.membro and getattr(termo.membro, 'telefone', None):
                enviar_whatsapp_template(termo.membro.telefone, 'lgpd_assinatura_pendente.txt', {'nome': termo.nome_completo, 'link_assinatura': link_assinatura})"""),
    ("""        enviar_email_html(
            destinatario=termo.email,
            assunto='Sua Segunda Via - Termo LGPD',
            template_name='midia_lgpd/email_segunda_via.html',
            context={'termo': termo, 'link_portal': request.build_absolute_uri('/')},
            anexos=[(pdf_name, pdf_content, 'application/pdf')]
        )""", """        enviar_email_html(
            destinatario=termo.email,
            assunto='Sua Segunda Via - Termo LGPD',
            template_name='midia_lgpd/email_segunda_via.html',
            context={'termo': termo, 'link_portal': request.build_absolute_uri('/')},
            anexos=[(pdf_name, pdf_content, 'application/pdf')]
        )
        if termo.membro and getattr(termo.membro, 'telefone', None):
            enviar_whatsapp_template(termo.membro.telefone, 'lgpd_segunda_via.txt', {'nome': termo.nome_completo})"""),
    ("""                enviar_email_html(
                    destinatario=termo.email,
                    assunto='Sua Segunda Via - Termo LGPD (Atualizado)',
                    template_name='midia_lgpd/email_segunda_via.html',
                    context={'termo': termo, 'link_portal': request.build_absolute_uri('/')},
                    anexos=[(pdf_name, pdf_content, 'application/pdf')]
                )""", """                enviar_email_html(
                    destinatario=termo.email,
                    assunto='Sua Segunda Via - Termo LGPD (Atualizado)',
                    template_name='midia_lgpd/email_segunda_via.html',
                    context={'termo': termo, 'link_portal': request.build_absolute_uri('/')},
                    anexos=[(pdf_name, pdf_content, 'application/pdf')]
                )
                if termo.membro and getattr(termo.membro, 'telefone', None):
                    enviar_whatsapp_template(termo.membro.telefone, 'lgpd_segunda_via.txt', {'nome': termo.nome_completo})"""),
    ("""            enviar_email_html(
                destinatario=membro.email,
                assunto=f'Acesso Liberado - {pasta.nome}',
                template_name='midia_lgpd/email_compartilhamento.html',
                context={'membro': membro, 'pasta': pasta, 'link_acesso': link_acesso}
            )""", """            enviar_email_html(
                destinatario=membro.email,
                assunto=f'Acesso Liberado - {pasta.nome}',
                template_name='midia_lgpd/email_compartilhamento.html',
                context={'membro': membro, 'pasta': pasta, 'link_acesso': link_acesso}
            )
            if getattr(membro, 'telefone', None):
                enviar_whatsapp_template(membro.telefone, 'casais_nova_mensagem.txt', {'membro': membro, 'pasta': pasta, 'link_acesso': link_acesso})""") # using a generic template just to have one
])

print("Patching more complete!")
