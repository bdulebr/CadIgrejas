from core.models import Membro

email = 'admin@pvenseada.org'
senha = 'LMAr261614@2025'

try:
    admin = Membro.objects.get(email=email)
    admin.set_password(senha)
    admin.is_superuser = True
    admin.is_staff = True
    admin.is_active = True
    admin.nivel_hierarquico = 'super_admin'
    admin.save()
    print("Senha do admin resetada com sucesso e privilegios garantidos!")
except Membro.DoesNotExist:
    admin = Membro.objects.create_superuser(
        email=email,
        password=senha,
        nome_completo='Administrador Master',
        cpf='000.000.000-00',
        telefone='(00) 00000-0000',
        nivel_hierarquico='super_admin'
    )
    print("Admin criado do zero com sucesso!")
