import os
import re

def refactor_almoxarifado():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/almoxarifado/views.py'
    if not os.path.exists(filepath):
        print("almoxarifado views.py does not exist")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from permissoes.decorators import requer_permissao' not in content:
        content = content.replace('from django.contrib.auth.decorators import login_required', 
                                  'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    # Find all @login_required and replace with @requer_permissao
    content = content.replace('@login_required\ndef', "@login_required\n@requer_permissao('almoxarifado', 'ver')\ndef")
    
    # Manually upgrade specific edit functions
    content = content.replace("@requer_permissao('almoxarifado', 'ver')\ndef novo_item", "@requer_permissao('almoxarifado', 'editar')\ndef novo_item")
    content = content.replace("@requer_permissao('almoxarifado', 'ver')\ndef editar_item", "@requer_permissao('almoxarifado', 'editar')\ndef editar_item")
    content = content.replace("@requer_permissao('almoxarifado', 'ver')\ndef excluir_item", "@requer_permissao('almoxarifado', 'excluir')\ndef excluir_item")
    content = content.replace("@requer_permissao('almoxarifado', 'ver')\ndef registrar_movimentacao", "@requer_permissao('almoxarifado', 'editar')\ndef registrar_movimentacao")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_almoxarifado()
print("Refactored almoxarifado/views.py")
