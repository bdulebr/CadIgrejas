import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from core.models import TemplateDocumento

def run():
    aviso_html = """<div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 40px;">
    <div style="text-align: center; border-bottom: 2px solid #0056b3; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="color: #0056b3; margin: 0;">PALAVRA DE VIDA ENSEADA</h1>
        <p style="margin: 5px 0 0; font-size: 14px; color: #666;">DEPARTAMENTO DE GESTÃO E LIDERANÇA</p>
    </div>
    
    <div style="margin-bottom: 30px;">
        <h2 style="text-align: center; font-size: 20px; text-decoration: underline;">COMUNICADO DE AÇÃO DISCIPLINAR: ADVERTÊNCIA</h2>
    </div>

    <p>Prezado(a) <strong>{{ membro.get_full_name }}</strong>,</p>
    
    <p>O Departamento de Liderança da Igreja Palavra de Vida Enseada vem, por meio deste documento formal, comunicar a aplicação de uma Advertência em virtude do seguinte motivo registrado:</p>
    
    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #d9534f; margin: 20px 0;">
        <p style="margin: 0; font-style: italic;">"{{ acao.motivo }}"</p>
    </div>
    
    <p>Ressaltamos que a vocação para servir é um compromisso firmado primeiramente com Deus e, em seguida, com o Corpo de Cristo. Nossos estatutos e diretrizes ministeriais exigem zelo, assiduidade e conduta cristã íntegra de todos os voluntários.</p>
    
    <p>Este documento serve como um registro formal e um chamado à reflexão e correção. Reiteramos nosso amor e compromisso com o seu crescimento espiritual, esperando que tal conduta não se repita no futuro.</p>
    
    <p style="margin-top: 40px;">No amor de Cristo,</p>
    
    <div style="margin-top: 50px; display: flex; justify-content: space-between;">
        <div style="text-align: center; width: 45%;">
            <hr style="border: 1px solid #333;" />
            <p style="margin: 5px 0 0;"><strong>{{ acao.autor.get_full_name }}</strong><br />Líder Responsável</p>
        </div>
        <div style="text-align: center; width: 45%;">
            <hr style="border: 1px solid #333;" />
            <p style="margin: 5px 0 0;"><strong>{{ membro.get_full_name }}</strong><br />Membro Notificado</p>
        </div>
    </div>
    
    <div style="margin-top: 40px; font-size: 11px; color: #888; text-align: center;">
        Documento gerado automaticamente pelo sistema de Gestão Administrativa Intranet.<br />
        Data de Emissão: {{ acao.data_aplicacao|date:"d/m/Y H:i" }}
    </div>
</div>"""

    TemplateDocumento.objects.get_or_create(
        nome_acao="carta_advertencia",
        defaults={'html_content': aviso_html, 'tipo': 'email', 'assunto_padrao': 'Comunicado de Ação Disciplinar: Advertência'}
    )

    susp_html = """<div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 40px;">
    <div style="text-align: center; border-bottom: 2px solid #0056b3; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="color: #0056b3; margin: 0;">PALAVRA DE VIDA ENSEADA</h1>
        <p style="margin: 5px 0 0; font-size: 14px; color: #666;">DEPARTAMENTO DE GESTÃO E LIDERANÇA</p>
    </div>
    
    <div style="margin-bottom: 30px;">
        <h2 style="text-align: center; font-size: 20px; text-decoration: underline;">COMUNICADO DE AÇÃO DISCIPLINAR: SUSPENSÃO</h2>
    </div>

    <p>Prezado(a) <strong>{{ membro.get_full_name }}</strong>,</p>
    
    <p>O Departamento de Liderança comunica formalmente o seu afastamento temporário (Suspensão) de todas as atividades e escalas ministeriais pelo seguinte motivo constatado:</p>
    
    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #d9534f; margin: 20px 0;">
        <p style="margin: 0; font-style: italic;">"{{ acao.motivo }}"</p>
    </div>
    
    <p>O período de suspensão inicia-se na data deste comunicado e se estenderá até <strong>{{ acao.data_fim_suspensao|date:"d/m/Y" }}</strong>.</p>
    
    <p>O afastamento disciplinar não é um ato punitivo no sentido mundano, mas um período estabelecido para descanso, reflexão, restauração espiritual e aconselhamento pastoral. Durante este período, incentivamos que continue congregando normalmente e buscando direcionamento.</p>
    
    <p style="margin-top: 40px;">Em oração por sua vida,</p>
    
    <div style="margin-top: 50px; display: flex; justify-content: space-between;">
        <div style="text-align: center; width: 45%;">
            <hr style="border: 1px solid #333;" />
            <p style="margin: 5px 0 0;"><strong>{{ acao.autor.get_full_name }}</strong><br />Líder Responsável</p>
        </div>
        <div style="text-align: center; width: 45%;">
            <hr style="border: 1px solid #333;" />
            <p style="margin: 5px 0 0;"><strong>{{ membro.get_full_name }}</strong><br />Membro Notificado</p>
        </div>
    </div>
</div>"""

    TemplateDocumento.objects.get_or_create(
        nome_acao="carta_suspensao",
        defaults={'html_content': susp_html, 'tipo': 'email', 'assunto_padrao': 'Comunicado de Ação Disciplinar: Suspensão'}
    )
    print("Templates criados com sucesso!")

if __name__ == '__main__':
    run()
