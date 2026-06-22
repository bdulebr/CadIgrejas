import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from escalas.pdf_generator import gerar_pdf_competencia
from escalas.models import CompetenciaEscala

comp = CompetenciaEscala.objects.filter(status='publicada').first()
if comp:
    success = gerar_pdf_competencia(comp.id)
    print(f"PDF generated: {success}")
else:
    print("No published competency found.")
