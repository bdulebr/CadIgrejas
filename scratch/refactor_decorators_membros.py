import os

def refactor_membros():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/gestao_membros/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required, user_passes_test', 
                                  'from django.contrib.auth.decorators import login_required, user_passes_test\nfrom permissoes.decorators import requer_permissao')
        content = content.replace('from django.contrib.auth.decorators import login_required', 
                                  'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    content = content.replace('@user_passes_test(is_super_admin)', "@requer_permissao('membros', 'editar')")
    content = content.replace('@user_passes_test(is_lider)', "@requer_permissao('membros', 'editar')")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_membros()
print("Refactored gestao_membros/views.py")
