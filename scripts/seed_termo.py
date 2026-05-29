import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from midia_lgpd.models import TermoLGPD

if not TermoLGPD.objects.filter(is_ativo=True).exists():
    TermoLGPD.objects.create(
        titulo="Termo de Consentimento para Uso de Imagem e Voz (LGPD)",
        conteudo_juridico="""Considerando os termos da Lei Geral de Proteção de Dados (Lei nº 13.709/2018), 
declaro que AUTORIZO o uso de minha imagem e voz em fotos e vídeos institucionais 
captados nas dependências e eventos oficiais da Igreja Palavra de Vida Enseada.

Esta autorização é concedida a título gratuito, isentando a instituição de quaisquer encargos,
e os arquivos poderão ser utilizados estritamente para fins de arquivo histórico,
divulgação interna na Intranet e eventuais comunicações oficiais.""",
        is_ativo=True
    )
    print("Termo base LGPD criado com sucesso!")
else:
    print("Já existe um termo ativo.")
