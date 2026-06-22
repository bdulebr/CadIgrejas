import os
import re

def refactor_escalas():
    filepath = 'C:/Users/MarcosLira/Desktop/Marcos/Projeto/escalas/views.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove user_passes_test import
    content = content.replace('from django.contrib.auth.decorators import login_required, user_passes_test', 'from django.contrib.auth.decorators import login_required\nfrom permissoes.decorators import requer_permissao')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_escalas()
print("Refactored escalas/views.py")
