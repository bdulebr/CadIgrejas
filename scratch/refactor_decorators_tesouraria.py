import os
import re

def refactor_tesouraria():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/tesouraria/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Import the new decorator
    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required', 
                                  'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Remove the tesouraria_required definition
    pattern_def = r'def tesouraria_required.*?return _wrapped_view'
    content = re.sub(pattern_def, '', content, flags=re.DOTALL)

    # Replace usages
    content = content.replace('@tesouraria_required', "@requer_permissao('tesouraria', 'ver')")

    # Specifically for create/update/delete views, change to 'editar' and 'excluir'
    content = content.replace("@requer_permissao('tesouraria', 'ver')\ndef novo_lancamento", "@requer_permissao('tesouraria', 'editar')\ndef novo_lancamento")
    content = content.replace("@requer_permissao('tesouraria', 'ver')\ndef editar_lancamento", "@requer_permissao('tesouraria', 'editar')\ndef editar_lancamento")
    content = content.replace("@requer_permissao('tesouraria', 'ver')\ndef excluir_lancamento", "@requer_permissao('tesouraria', 'excluir')\ndef excluir_lancamento")
    content = content.replace("@requer_permissao('tesouraria', 'ver')\ndef salvar_lote", "@requer_permissao('tesouraria', 'editar')\ndef salvar_lote")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_tesouraria()
print("Refactored tesouraria/views.py")
