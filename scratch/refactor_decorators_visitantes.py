import os
import re

def refactor_visitantes():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/visitantes/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required', 
                                  'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Find all @login_required and replace with @requer_permissao
    content = content.replace('@login_required\ndef', "@login_required\n@requer_permissao('visitantes', 'ver')\ndef")
    
    # Manually upgrade specific edit functions
    content = content.replace("@requer_permissao('visitantes', 'ver')\ndef visitante_criar", "@requer_permissao('visitantes', 'editar')\ndef visitante_criar")
    content = content.replace("@requer_permissao('visitantes', 'ver')\ndef visitante_editar", "@requer_permissao('visitantes', 'editar')\ndef visitante_editar")
    content = content.replace("@requer_permissao('visitantes', 'ver')\ndef visitante_excluir", "@requer_permissao('visitantes', 'excluir')\ndef visitante_excluir")
    content = content.replace("@requer_permissao('visitantes', 'ver')\ndef registrar_acompanhamento", "@requer_permissao('visitantes', 'editar')\ndef registrar_acompanhamento")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_visitantes()
print("Refactored visitantes/views.py")
