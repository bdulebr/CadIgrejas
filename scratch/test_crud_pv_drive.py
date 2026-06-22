import os
import django
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from core.models import Membro
from midia_lgpd.models import PastaVirtual
from midia_lgpd.views import criar_pasta, renomear_pasta, excluir_pasta

print("=== INICIANDO TESTE CRUD PV DRIVE ===")

# Pegar usuario de teste
user = Membro.objects.first()
if not user:
    print("Nenhum usuario encontrado. Teste abortado.")
    exit(1)

# Encontrar pasta raiz
raiz = PastaVirtual.objects.filter(tipo_pasta='usuario', dono_membro=user).first()
if not raiz:
    print("Pasta raiz não encontrada. Teste abortado.")
    exit(1)

factory = RequestFactory()

def create_request(url, method='POST', data=None):
    if method == 'POST':
        request = factory.post(url, data=data)
    else:
        request = factory.get(url)
    request.user = user
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request

print("1. Criando Pasta de Teste...")
request = create_request('/drive/pasta/criar/', data={'nome': 'Pasta Teste CRUD', 'parent_id': raiz.id, 'modo_atual': 'pessoal'})
response = criar_pasta(request)
print("Criada com sucesso!" if response.status_code == 302 else f"Erro ao criar: {response.status_code}")

# Verificar DB
pasta_teste = PastaVirtual.objects.filter(nome='Pasta Teste CRUD', parent=raiz).first()
if not pasta_teste:
    print("FALHA: Pasta nao encontrada no DB!")
    exit(1)
print(f"Pasta encontrada: {pasta_teste.id} - {pasta_teste.nome}")

print("2. Renomeando Pasta...")
request = create_request(f'/drive/pasta/renomear/{pasta_teste.id}/', data={'nome': 'Pasta Teste CRUD Renomeada'})
response = renomear_pasta(request, pasta_id=pasta_teste.id)
print("Renomeada com sucesso!" if response.status_code == 302 else f"Erro ao renomear: {response.status_code}")

# Verificar DB
pasta_teste.refresh_from_db()
print(f"Novo nome: {pasta_teste.nome}")
if pasta_teste.nome != 'Pasta Teste CRUD Renomeada':
    print("FALHA: Nome nao alterado!")
    exit(1)

print("3. Excluindo Pasta...")
request = create_request(f'/drive/pasta/excluir/{pasta_teste.id}/')
response = excluir_pasta(request, pasta_id=pasta_teste.id)
print("Excluida com sucesso!" if response.status_code == 302 else f"Erro ao excluir: {response.status_code}")

# Verificar DB
pasta_teste.refresh_from_db()
print(f"is_excluida: {pasta_teste.is_excluida}")
if not pasta_teste.is_excluida:
    print("FALHA: Pasta nao foi marcada como excluida!")
    exit(1)

print("=== TESTE CRUD COMPLETO E BEM SUCEDIDO ===")
