import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from core.models import Membro

def criar_usuarios():
    # Marcos (Super-admin)
    if not Membro.objects.filter(email='marcos@pvenseada.org').exists():
        marcos = Membro.objects.create_superuser(
            username='marcos@pvenseada.org',
            email='marcos@pvenseada.org',
            password='LMar261614@2025',
            first_name='Marcos Roberto',
            last_name='Lira',
            nivel_hierarquico='super_admin'
        )
        print("Super-admin Marcos criado com sucesso.")
    else:
        print("Usuário Marcos já existe.")

    # Paula (Líder das Escalas)
    if not Membro.objects.filter(email='paula@pvenseada.org').exists():
        paula = Membro.objects.create_user(
            username='paula@pvenseada.org',
            email='paula@pvenseada.org',
            password='123456789',
            first_name='Paula',
            last_name='Fernanda',
            nivel_hierarquico='lider'
        )
        print("Líder Paula criada com sucesso.")
    else:
        print("Usuária Paula já existe.")

    # Douglas (Líder Almoxarifado)
    if not Membro.objects.filter(email='douglas@pvenseada.org').exists():
        douglas = Membro.objects.create_user(
            username='douglas@pvenseada.org',
            email='douglas@pvenseada.org',
            password='123456789',
            first_name='Douglas',
            nivel_hierarquico='lider'
        )
        print("Líder Douglas criado com sucesso.")
    else:
        print("Usuário Douglas já existe.")

if __name__ == '__main__':
    criar_usuarios()
