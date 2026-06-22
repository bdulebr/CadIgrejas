import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from escalas.models import CultoEvento

for c in CultoEvento.objects.all():
    print(c.id, c.nome, c.chave_slug)
