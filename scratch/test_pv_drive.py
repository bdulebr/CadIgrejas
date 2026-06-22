import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from midia_lgpd.models import PastaVirtual, ArquivoMidia
from core.models import Membro
from gestao_membros.models import Departamento

# Tenta pegar um membro qualquer
membro = Membro.objects.first()

print(f"Iniciando testes com o membro: {membro.first_name}")

# 1. Criação de Pasta
print("1. Criando pasta...")
pasta = PastaVirtual.objects.create(
    nome="Pasta de Teste Automatizado",
    criado_por=membro
)
print(f"Pasta criada no banco: {pasta.nome} (ID GDrive: {pasta.gdrive_folder_id})")

# 2. Edição de Pasta
print("2. Editando pasta...")
pasta.nome = "Pasta Editada Teste Automatizado"
pasta.save()
print(f"Pasta renomeada para: {pasta.nome}")

# 3. Envio de Arquivo
print("3. Enviando arquivo para a pasta...")
file_content = b"Conteudo de teste para GDrive."
test_file = SimpleUploadedFile("arquivo_teste.txt", file_content, content_type="text/plain")

arquivo = ArquivoMidia.objects.create(
    pasta=pasta,
    titulo="arquivo_teste.txt",
    arquivo=test_file,
    tamanho_bytes=len(file_content),
    extensao='.txt',
    enviado_por=membro
)
print(f"Arquivo criado no banco: {arquivo.titulo} (ID GDrive: {arquivo.gdrive_file_id})")

# 4. Edição de Arquivo (Renomear)
print("4. Editando arquivo...")
arquivo.titulo = "arquivo_teste_editado.txt"
arquivo.save()
print(f"Arquivo renomeado para: {arquivo.titulo}")

# 5. Exclusão de Arquivo
print("5. Excluindo arquivo...")
arquivo_id = arquivo.id
arquivo.delete()
print(f"Arquivo {arquivo_id} excluído com sucesso do banco (e do GDrive via signals).")

# 6. Exclusão de Pasta
print("6. Excluindo pasta...")
pasta_id = pasta.id
pasta.delete()
print(f"Pasta {pasta_id} excluída com sucesso do banco (e do GDrive via signals).")

print("TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
