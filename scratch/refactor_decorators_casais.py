import os
import re

def refactor_casais():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/ministerio_casais/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required', 
                                  'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Remove the def check_permission
    pattern_def = r'def check_permission.*?return False'
    content = re.sub(pattern_def, '', content, flags=re.DOTALL)

    # Replace inline checks with decorator
    # The structure is usually:
    # @login_required
    # def func_name(request, ...):
    #     if not check_permission(request.user):
    #         return HttpResponse(...)
    
    # We will replace "@login_required\ndef" with "@login_required\n@requer_permissao('casais', 'ver')\ndef"
    content = content.replace('@login_required\ndef', "@login_required\n@requer_permissao('casais', 'ver')\ndef")

    # We also need to strip out the inline check lines
    pattern_inline = r'if not check_permission\(request\.user\):\n\s*return HttpResponse\([^)]+\)'
    content = re.sub(pattern_inline, '', content)
    
    # We also need to strip out the inline check lines that might use redirect
    pattern_inline_redirect = r'if not check_permission\(request\.user\):\n\s*messages\.error\([^)]+\)\n\s*return redirect\([^)]+\)'
    content = re.sub(pattern_inline_redirect, '', content)
    
    # Also for specific actions we upgrade to 'editar' and 'excluir'
    content = content.replace("@requer_permissao('casais', 'ver')\ndef criar_casal", "@requer_permissao('casais', 'editar')\ndef criar_casal")
    content = content.replace("@requer_permissao('casais', 'ver')\ndef editar_casal", "@requer_permissao('casais', 'editar')\ndef editar_casal")
    content = content.replace("@requer_permissao('casais', 'ver')\ndef registrar_aconselhamento", "@requer_permissao('casais', 'editar')\ndef registrar_aconselhamento")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_casais()
print("Refactored ministerio_casais/views.py")
