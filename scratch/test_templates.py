import os
import django
from django.template.loader import render_to_string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

templates = [
    'emails/boas_vindas.html',
    'emails/nova_escala.html',
    'emails/escala_atualizada.html',
    'emails/escala_cancelada.html',
    'emails/termo_lgpd.html',
    'emails/novo_aviso.html',
    'emails/promocao_hierarquica.html',
    'emails/lembrete_curso.html',
    'gestao_membros/email_boas_vindas.html',
    'ministerio_casais/email_boas_vindas_casal.html',
    'visitantes/email_boas_vindas.html',
    'visitantes/email_novo_membro.html',
]

context = {
    'nome': 'Membro Teste',
    'email': 'teste@teste.com',
    'senha': 'senha',
    'link_acesso': '#',
    'departamento': 'Recepção',
    'mes': '06',
    'ano': '2026',
    'titulo_aviso': 'Aviso de Teste',
    'novo_nivel': 'Líder',
    'titulo_curso': 'Curso de Teste',
    'data_aula': '20/06/2026',
    'local_aula': 'Sede',
    'base_url': 'http://localhost'
}

print("Verificando renderização dos templates de e-mail...")
for t in templates:
    try:
        render_to_string(t, context)
        print(f"[OK] {t}")
    except Exception as e:
        print(f"[ERRO] {t}: {e}")

print("Concluído!")
