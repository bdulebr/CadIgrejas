import os
import re

def refactor_escalas():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/escalas/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required, user_passes_test', 
                                  'from django.contrib.auth.decorators import login_required, user_passes_test\nfrom permissoes.decorators import requer_permissao')

    # Replace @user_passes_test(is_lider) and is_super_admin_escala
    # We will assume everything here belongs to 'escalas' module.
    # To be safe, we will use 'editar' for all leader actions in scales, since a leader essentially edits scales.
    content = content.replace('@user_passes_test(is_lider)', "@requer_permissao('escalas', 'editar')")
    content = content.replace('@user_passes_test(is_super_admin_escala)', "@requer_permissao('escalas', 'editar')")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_escalas()
print("Refactored escalas/views.py")
