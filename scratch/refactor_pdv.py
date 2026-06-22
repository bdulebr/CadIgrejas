import os
import re

def refactor_pdv():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/pdv/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove user_passes_test import
    content = content.replace('from django.contrib.auth.decorators import login_required, user_passes_test', 'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Replace @user_passes_test(pdv_access_check) with @requer_permissao('pdv', 'ver')
    content = content.replace('@user_passes_test(pdv_access_check)', "@requer_permissao('pdv', 'ver')")

    # Replace @user_passes_test(sysadmin_access_check) with @requer_permissao('pdv', 'excluir')
    content = content.replace('@user_passes_test(sysadmin_access_check)', "@requer_permissao('pdv', 'excluir')")

    # Also for specific actions
    content = content.replace("@requer_permissao('pdv', 'ver')\ndef criar_venda", "@requer_permissao('pdv', 'editar')\ndef criar_venda")
    content = content.replace("@requer_permissao('pdv', 'ver')\ndef finalizar_venda", "@requer_permissao('pdv', 'editar')\ndef finalizar_venda")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_pdv()
print("Refactored pdv/views.py")
