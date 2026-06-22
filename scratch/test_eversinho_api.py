import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_eversinho():
    print("Iniciando Teste do Eversinho IA...")
    client = Client()
    User = get_user_model()
    
    # 1. Obter/Criar um usuario para logar (a view exige @login_required)
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('testadmin', 'admin@admin.com', 'admin')
    
    client.force_login(user)
    
    # 2. Enviar requisição POST para a API do Eversinho
    print("Enviando requisição POST para /api/eversinho/chat/...")
    response = client.post('/api/eversinho/chat/', {
        'mensagem': 'Como eu cadastro pessoas?'
    })
    
    print(f"Status Code: {response.status_code}")
    print("--- Corpo da Resposta ---")
    print(response.content.decode('utf-8'))
    print("-------------------------")
    
    if response.status_code == 200:
        print("✅ Rota da API respondeu com 200 OK.")
        if "bg-gray-800" in response.content.decode('utf-8'):
            print("✅ Resposta HTML gerada com sucesso (Bolhas do Chat presentes).")
        else:
            print("❌ HTML não continha as classes esperadas da bolha.")
    else:
        print("❌ Falha na rota. Status diferente de 200.")

if __name__ == '__main__':
    test_eversinho()
