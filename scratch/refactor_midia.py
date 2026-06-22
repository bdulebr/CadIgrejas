import os
import re

def refactor_midia_lgpd():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/midia_lgpd/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove user_passes_test import
    content = content.replace('from django.contrib.auth.decorators import login_required, user_passes_test', 'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Replace @user_passes_test(is_super_admin) with @requer_permissao('midia_lgpd', 'excluir')
    # Because sysadmin functions in midia_lgpd are typically deletion or config
    content = content.replace('@user_passes_test(is_super_admin)', "@requer_permissao('midia_lgpd', 'excluir')")

    # Assuming all other views are @login_required
    content = content.replace('@login_required\ndef', "@login_required\n@requer_permissao('midia_lgpd', 'ver')\ndef")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_midia_lgpd()
print("Refactored midia_lgpd/views.py")
