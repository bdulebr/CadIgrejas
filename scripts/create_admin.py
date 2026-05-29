import os
import django

# Carregar o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from core.models import Membro

email_admin = 'admin@pvenseada.org'
senha_admin = 'admin123'

if not Membro.objects.filter(email=email_admin).exists():
    admin = Membro(
        username='admin',
        email=email_admin,
        first_name='Marcos',
        last_name='Lira (Admin)',
        nivel_hierarquico='super_admin',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    admin.set_password(senha_admin)
    admin.save()
    print("USUARIO CRIADO COM SUCESSO!")
else:
    admin = Membro.objects.get(email=email_admin)
    admin.nivel_hierarquico = 'super_admin'
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password(senha_admin)
    admin.save()
    print("USUARIO ATUALIZADO COM SUCESSO!")
