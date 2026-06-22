import os
import re

def create_template(filename, content):
    path = os.path.join('core', 'templates', 'whatsapp', filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

create_template('casais_matricula_curso.txt', "Olá! O casal foi matriculado no curso: {{ curso.nome }}.\nAcesse o painel para mais informações.")
create_template('casais_curso_concluido.txt', "Parabéns! O casal concluiu o curso: {{ curso.nome }}.\nAcesse o painel para baixar o certificado.")
create_template('visitante_boas_vindas.txt', "Olá {{ nome }}, seja muito bem-vindo(a) à Palavra de Vida!\nAcesse nossa plataforma: {{ base_url }}")
create_template('visitante_novo_membro.txt', "Olá {{ nome }}, bem-vindo(a) à Família Palavra de Vida Sede como novo membro!\n{{ base_url }}")
create_template('membro_boas_vindas.txt', "Olá {{ nome }}! Seu acesso à Intranet foi liberado.\nLogin: {{ email }}\nSenha provisória: {{ senha }}\nAcesse: {{ link_acesso }}")
create_template('email_acesso_casal.txt', "Olá {{ casal.nome_formatado }}! Aqui estão os detalhes de acesso ao seu curso.\nPor favor, verifique sua conta na plataforma.")

def patch_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if "from intranet.services.whatsapp_service import enviar_whatsapp_template" not in content:
        # Add import at the top
        content = content.replace("from intranet.services.gmail_service import enviar_email_html",
                                  "from intranet.services.gmail_service import enviar_email_html\nfrom intranet.services.whatsapp_service import enviar_whatsapp_template")

    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: {old[:30]}... not found in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


# 1. gestao_membros/views.py
patch_file("gestao_membros/views.py", [
    ("""        enviar_email_html(
            destinatario=membro.email,
            assunto='Bem-vindo ao Sistema - Credenciais de Acesso',
            template_name='gestao_membros/email_boas_vindas.html',
            context=context
        )""", """        enviar_email_html(
            destinatario=membro.email,
            assunto='Bem-vindo ao Sistema - Credenciais de Acesso',
            template_name='gestao_membros/email_boas_vindas.html',
            context=context
        )
        if getattr(membro, 'telefone', None):
            enviar_whatsapp_template(membro.telefone, 'membro_boas_vindas.txt', context)""")
])

# 2. visitantes/views.py
patch_file("visitantes/views.py", [
    ("""        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo(a) à Palavra de Vida!',
            template_name='visitantes/email_boas_vindas.html',
            context={'nome': nome, 'base_url': base_url}
        )""", """        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo(a) à Palavra de Vida!',
            template_name='visitantes/email_boas_vindas.html',
            context={'nome': nome, 'base_url': base_url}
        )
        # Tenta pegar telefone do kwargs ou de uma global de visitante. Se nao, n envia. Aqui recebemos só email e nome. Mas lá na call (line 184) temos o visitante.
        # Nao temos o model visitante aqui, pois passa `nome` e `email`.
        pass"""),
    ("""def enviar_email_boas_vindas_background(nome, email, base_url):""", """def enviar_email_boas_vindas_background(nome, email, base_url, telefone=None):"""),
    ("""def enviar_email_novo_membro_background(nome, email, base_url):""", """def enviar_email_novo_membro_background(nome, email, base_url, telefone=None):"""),
    ("""            threading.Thread(target=enviar_email_boas_vindas_background, args=(nome_completo, email, base_url)).start()""", """            threading.Thread(target=enviar_email_boas_vindas_background, args=(nome_completo, email, base_url, visitante.telefone)).start()"""),
    ("""            threading.Thread(target=enviar_email_novo_membro_background, args=(visitante.nome_completo, visitante.email, base_url)).start()""", """            threading.Thread(target=enviar_email_novo_membro_background, args=(visitante.nome_completo, visitante.email, base_url, visitante.telefone)).start()"""),
    ("""        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo à Família Palavra de Vida Sede!',
            template_name='visitantes/email_novo_membro.html',
            context={'nome': nome, 'base_url': base_url}
        )""", """        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo à Família Palavra de Vida Sede!',
            template_name='visitantes/email_novo_membro.html',
            context={'nome': nome, 'base_url': base_url}
        )
        if telefone:
            enviar_whatsapp_template(telefone, 'visitante_novo_membro.txt', {'nome': nome, 'base_url': base_url})"""),
])

# For visitantes email boas vindas inside function
with open("visitantes/views.py", "r", encoding="utf-8") as f:
    vc = f.read()
vc = vc.replace("""        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo(a) à Palavra de Vida!',
            template_name='visitantes/email_boas_vindas.html',
            context={'nome': nome, 'base_url': base_url}
        )
        # Tenta pegar telefone""", """        enviar_email_html(
            destinatario=email,
            assunto='Bem-vindo(a) à Palavra de Vida!',
            template_name='visitantes/email_boas_vindas.html',
            context={'nome': nome, 'base_url': base_url}
        )
        if telefone:
            enviar_whatsapp_template(telefone, 'visitante_boas_vindas.txt', {'nome': nome, 'base_url': base_url})
        # Tenta pegar telefone""")
with open("visitantes/views.py", "w", encoding="utf-8") as f:
    f.write(vc)


# 3. ministerio_casais/views.py
patch_file("ministerio_casais/views.py", [
    ("""                        enviar_email_html(e, ass, 'ministerio_casais/email_matricula_curso.html', ctx)""", """                        enviar_email_html(e, ass, 'ministerio_casais/email_matricula_curso.html', ctx)
                        # WhatsApp para casal (ambos telefones se disponíveis)
                        t1 = ctx.get('casal').telefone_1
                        t2 = ctx.get('casal').telefone_2
                        if t1: enviar_whatsapp_template(t1, 'casais_matricula_curso.txt', ctx)
                        if t2 and t2 != t1: enviar_whatsapp_template(t2, 'casais_matricula_curso.txt', ctx)"""),
    ("""                    enviar_email_html(e, ass, 'ministerio_casais/email_curso_concluido.html', ctx)""", """                    enviar_email_html(e, ass, 'ministerio_casais/email_curso_concluido.html', ctx)
                    t1 = ctx.get('casal').telefone_1
                    t2 = ctx.get('casal').telefone_2
                    if t1: enviar_whatsapp_template(t1, 'casais_curso_concluido.txt', ctx)
                    if t2 and t2 != t1: enviar_whatsapp_template(t2, 'casais_curso_concluido.txt', ctx)"""),
])

# 4. ministerio_casais/views_professores.py
patch_file("ministerio_casais/views_professores.py", [
    ("""            enviar_email_html(
                destinatario=e,
                assunto=assunto,
                template_name='ministerio_casais/email_acesso_aluno.html',
                context=contexto_email
            )""", """            enviar_email_html(
                destinatario=e,
                assunto=assunto,
                template_name='ministerio_casais/email_acesso_aluno.html',
                context=contexto_email
            )
            t1 = casal.telefone_1
            t2 = casal.telefone_2
            if t1: enviar_whatsapp_template(t1, 'email_acesso_casal.txt', contexto_email)
            if t2 and t2 != t1: enviar_whatsapp_template(t2, 'email_acesso_casal.txt', contexto_email)""")
])

print("Patching complete!")
