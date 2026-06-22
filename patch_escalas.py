import re

with open("escalas/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Adiciona o import se não existir
if "enviar_whatsapp_template" not in content:
    content = content.replace("from intranet.services.gmail_service import enviar_email_html",
                              "from intranet.services.gmail_service import enviar_email_html\nfrom intranet.services.whatsapp_service import enviar_whatsapp_template")

# Atualização de Escala (linha 357 aprox)
#       enviar_email_html(membro.email, f"Atualização de Escala - {comp.departamento.nome}", "escala_atualizada.html", {
# ... })
pattern1 = re.compile(r"(enviar_email_html\([^,]+,\s*(?:f?\".*?\"),\s*\"(.*?)\",\s*\{.*?\})\)", re.DOTALL)

def replace_with_whatsapp(match):
    original = match.group(0)
    template_name = match.group(2)
    # The context is the 4th argument. We can capture everything inside the { ... }

    # Simple heuristic: we just add a new line after the original call
    return original + f"""
                    if membro.telefone:
                        enviar_whatsapp_template(membro.telefone, "{template_name}", {{
                            'nome': membro.first_name,
                            'departamento': comp.departamento.nome if hasattr(comp, 'departamento') else departamento_nome if 'departamento_nome' in locals() else departamento,
                            'link_painel': f"{{settings.BASE_URL}}/minhas-escalas/"
                        }})"""

# We'll just replace specific blocks manually for safety.
content = content.replace("""                    enviar_email_html(membro.email, f"Atualização de Escala - {comp.departamento.nome}", "escala_atualizada.html", {
                        'nome': membro.first_name,
                        'departamento': comp.departamento.nome,
                        'departamento_logo': '',
                        'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                    })""", """                    enviar_email_html(membro.email, f"Atualização de Escala - {comp.departamento.nome}", "escala_atualizada.html", {
                        'nome': membro.first_name,
                        'departamento': comp.departamento.nome,
                        'departamento_logo': '',
                        'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                    })
                    if getattr(membro, 'telefone', None):
                        enviar_whatsapp_template(membro.telefone, "escala_atualizada.txt", {
                            'nome': membro.first_name,
                            'departamento': comp.departamento.nome,
                            'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                        })""")

content = content.replace("""            enviar_email_html(membro.email, f"Cancelamento de Escala - {departamento}", "escala_cancelada.html", {
                'nome': membro.first_name,
                'departamento': departamento,
                'departamento_logo': '',
                'data': data_escala,
                'horario_inicio': horario_inicio,
                'horario_fim': horario_fim,
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })""", """            enviar_email_html(membro.email, f"Cancelamento de Escala - {departamento}", "escala_cancelada.html", {
                'nome': membro.first_name,
                'departamento': departamento,
                'departamento_logo': '',
                'data': data_escala,
                'horario_inicio': horario_inicio,
                'horario_fim': horario_fim,
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })
            if getattr(membro, 'telefone', None):
                enviar_whatsapp_template(membro.telefone, "escala_cancelada.txt", {
                    'nome': membro.first_name,
                    'departamento': departamento,
                    'data': data_escala,
                    'horario_inicio': horario_inicio,
                    'horario_fim': horario_fim,
                    'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                })""")

content = content.replace("""            enviar_email_html(membro.email, f"Nova Escala Oficial - {comp.departamento.nome}", "nova_escala.html", {
                'nome': membro.first_name,
                'departamento': comp.departamento.nome,
                'departamento_logo': '',
                'data': comp.mes_ano,
                'horario_inicio': "Vários",
                'horario_fim': "Vários",
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })""", """            enviar_email_html(membro.email, f"Nova Escala Oficial - {comp.departamento.nome}", "nova_escala.html", {
                'nome': membro.first_name,
                'departamento': comp.departamento.nome,
                'departamento_logo': '',
                'data': comp.mes_ano,
                'horario_inicio': "Vários",
                'horario_fim': "Vários",
                'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
            })
            if getattr(membro, 'telefone', None):
                enviar_whatsapp_template(membro.telefone, "nova_escala.txt", {
                    'nome': membro.first_name,
                    'departamento': comp.departamento.nome,
                    'data': comp.mes_ano,
                    'link_painel': f"{settings.BASE_URL}/minhas-escalas/"
                })""")


with open("escalas/views.py", "w", encoding="utf-8") as f:
    f.write(content)
print("escalas/views.py PATCHED!")
