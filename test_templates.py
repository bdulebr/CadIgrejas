import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO

# Dummy data for the templates
class DummyCasal:
    nomes_juntos = "Marcos & Esposa"

class DummyVisitante:
    nome_completo = "Marcos Lira"
    telefone = "(11) 99999-9999"
    email = "marcosgja93@gmail.com"
    origem = "Redes Sociais"
    data_visita = timezone.now().date()
    status = "Novo"

    class DummyUser:
        first_name = "Admin"
        username = "admin"

    cadastrado_por = DummyUser()

class DummyCurso:
    nome = "Curso Casados Para Sempre"
    data_inicio = timezone.now().date()
    carga_horaria = 12

class DummyItem:
    nome = "Microfone Shure"
    id_unico = "MIC-12345"

class DummyMovimentacao:
    data_hora = timezone.now()
    nome_digitado = "Marcos"
    email_digitado = "marcosgja93@gmail.com"
    tipo = "retirada"
    quantidade = 1
    item = DummyItem()
    assinatura_digital_hash = "abcdef1234567890"

from email.mime.image import MIMEImage

def enviar_email(assunto, template_path, contexto):
    html_content = render_to_string(template_path, contexto)
    msg = EmailMultiAlternatives(assunto, "Visualize o email em um cliente HTML", settings.DEFAULT_FROM_EMAIL, ["marcosgja93@gmail.com"])
    msg.attach_alternative(html_content, "text/html")

    # Embutir logo como CID para o Gmail não bloquear nem tentar acessar localhost
    try:
        with open(logo_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<logo_igreja>')
            img.add_header('Content-Disposition', 'inline', filename='logo.jpg')
            msg.attach(img)
    except Exception as e:
        print(f"Aviso: não foi possível embutir a logo: {e}")

    msg.send()
    print(f"E-mail {template_path} enviado com sucesso!")

def gerar_pdf(template_path, contexto, output_filename):
    html_str = render_to_string(template_path, contexto)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_str.encode("UTF-8")), result)
    if not pdf.err:
        with open(os.path.join(settings.BASE_DIR, output_filename), 'wb') as f:
            f.write(result.getvalue())
        print(f"PDF {output_filename} salvo na raiz do projeto!")
    else:
        print(f"Erro ao gerar PDF {output_filename}")

logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'logo.jpg')
base_url = "http://localhost:8000"
logo_url = "cid:logo_igreja"

# Testar E-mails
print("Enviando e-mails de teste...")
try:
    enviar_email("Bem-vindo(a) à Palavra de Vida!", "visitantes/email_boas_vindas.html", {"nome": "Marcos Lira", "base_url": base_url, "logo_url": logo_url})
    enviar_email("Você agora é Membro Oficial!", "visitantes/email_novo_membro.html", {"visitante": DummyVisitante(), "base_url": base_url, "logo_url": logo_url})
    enviar_email("Bem-vindos ao Ministério de Casais!", "ministerio_casais/email_boas_vindas_casal.html", {"casal": DummyCasal(), "base_url": base_url, "logo_url": logo_url})
    enviar_email("Lembrete: Seu curso começa amanhã!", "ministerio_casais/email_lembrete_curso.html", {"casal": DummyCasal(), "curso": DummyCurso(), "base_url": base_url, "logo_url": logo_url})
    enviar_email("Matrícula Confirmada!", "ministerio_casais/email_matricula_curso.html", {"casal": DummyCasal(), "curso": DummyCurso(), "base_url": base_url, "logo_url": logo_url})
    enviar_email("Parabéns pela Conclusão do Curso!", "ministerio_casais/email_curso_concluido.html", {"casal": DummyCasal(), "curso": DummyCurso(), "base_url": base_url, "logo_url": logo_url})
except Exception as e:
    print(f"Erro ao enviar emails: {e}")

# Testar PDFs
print("Gerando PDFs de teste...")
gerar_pdf("visitantes/pdf_relatorio_geral.html", {"data_geracao": timezone.now(), "logo_path": logo_path}, "teste_visitantes_relatorio_geral.pdf")
gerar_pdf("visitantes/pdf_relatorio_individual.html", {"visitante": DummyVisitante(), "data_geracao": timezone.now(), "logo_path": logo_path}, "teste_visitantes_relatorio_individual.pdf")
gerar_pdf("ministerio_casais/pdf_relatorio_geral.html", {"data_geracao": timezone.now(), "logo_path": logo_path}, "teste_casais_relatorio_geral.pdf")
gerar_pdf("ministerio_casais/pdf_relatorio_individual.html", {"casal": DummyCasal(), "data_geracao": timezone.now(), "logo_path": logo_path}, "teste_casais_relatorio_individual.pdf")
gerar_pdf("ministerio_casais/pdf_certificado.html", {"casal": DummyCasal(), "logo_path": logo_path}, "teste_casais_certificado.pdf")
gerar_pdf("almoxarifado/termo_cautela_pdf.html", {"movimentacoes": [DummyMovimentacao()], "nome_usuario": "Marcos Lira", "data": timezone.now(), "logo_path": logo_path}, "teste_almoxarifado_termo.pdf")
gerar_pdf("almoxarifado/etiqueta_qr_pdf.html", {"item": DummyItem(), "qr_retirar_b64": "dummy", "qr_devolver_b64": "dummy", "logo_path": logo_path}, "teste_almoxarifado_etiqueta.pdf")
gerar_pdf("almoxarifado/pdf_livro_fallback.html", {"movimentacoes": [DummyMovimentacao()], "logo_path": logo_path}, "teste_almoxarifado_livro.pdf")

print("Testes concluídos!")
