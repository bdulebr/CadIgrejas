import os
import django
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from midia_lgpd.models import DocumentoTemplate

def criar_template_email(identificador, titulo, descricao, campos_json, conteudo_interno):
    html_base = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; color: #334155;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #1e40af; color: #ffffff; padding: 30px; text-align: center;">
                <img src="{{{{IGREJA_LOGO}}}}" alt="Logo da Igreja" style="max-height: 80px; margin-bottom: 10px; border-radius: 8px; display: block; margin: 0 auto;">
                <h1 style="margin: 15px 0 0 0; font-size: 24px; font-weight: bold;">{titulo.replace('E-mail: ', '')}</h1>
            </div>
            <div style="padding: 30px;">
                {conteudo_interno}
            </div>
            <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
                <p><strong>{{{{IGREJA_NOME}}}}</strong> - CNPJ: {{{{IGREJA_CNPJ}}}}</p>
                <p>Esta é uma mensagem automática da Intranet PVE. Por favor, não responda este e-mail.</p>
            </div>
        </div>
    </div>
    """
    
    campos_base = [
        {'nome': 'IGREJA_LOGO', 'label': 'Logo da Igreja (URL)'},
        {'nome': 'IGREJA_NOME', 'label': 'Nome da Igreja'},
        {'nome': 'IGREJA_CNPJ', 'label': 'CNPJ da Igreja'}
    ]
    campos_json.extend(campos_base)
    
    DocumentoTemplate.objects.update_or_create(
        identificador_sistema=identificador,
        defaults={
            'titulo': titulo,
            'descricao': descricao,
            'tipo_documento': 'email',
            'conteudo_base': html_base,
            'html_canva': html_base,
            'campos_json': campos_json
        }
    )
    print(f" - {titulo} criado.")

def run():
    print("Iniciando seeder de templates unificado...")
    
    # 1. PDF Escala
    html_escala = """
    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px;">
        <table width="100%" style="margin-bottom: 20px;">
            <tr>
                <td width="20%" style="text-align: center;">
                    <img src="{{IGREJA_LOGO}}" style="max-height: 80px;">
                </td>
                <td width="60%" style="text-align: center;">
                    <h1 style="color: #1e3a8a; font-size: 24px; margin: 0;">Escala Oficial</h1>
                    <h2 style="color: #4b5563; font-size: 16px; margin: 5px 0;">{{NOME_DEPARTAMENTO}} - Competência: {{COMPETENCIA}}</h2>
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">{{IGREJA_NOME}} - CNPJ: {{IGREJA_CNPJ}}</p>
                </td>
                <td width="20%" style="text-align: center;">
                    <img src="{{DEPARTAMENTO_LOGO}}" style="max-height: 80px;">
                </td>
            </tr>
        </table>
        
        <hr style="border: 0; border-top: 2px solid #1e3a8a; margin-bottom: 20px;">
        
        {{ESCALA_TABELA_HTML}}
        
        <div style="margin-top: 30px; text-align: center; color: #9ca3af; font-size: 10px;">
            <p>Gerado automaticamente pela Intranet PVE</p>
        </div>
    </div>
    """
    
    css_escala = """
    table.tabela-escala { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }
    table.tabela-escala th { background-color: #2563eb; color: white; padding: 10px; text-align: center; font-weight: bold; border: 1px solid #1d4ed8; }
    table.tabela-escala td { padding: 8px; text-align: center; border: 1px solid #cbd5e1; }
    table.tabela-escala tr:nth-child(even) { background-color: #f8fafc; }
    table.tabela-escala tr:nth-child(odd) { background-color: #ffffff; }
    """
    
    DocumentoTemplate.objects.update_or_create(
        identificador_sistema='pdf_escala_padrao',
        defaults={
            'titulo': 'PDF Padrão - Escala de Voluntários',
            'descricao': 'Layout oficial gerado quando o líder exporta a escala.',
            'tipo_documento': 'pdf_escala',
            'conteudo_base': html_escala,
            'html_canva': html_escala,
            'css_canva': css_escala,
            'campos_json': [
                {'nome': 'IGREJA_LOGO', 'label': 'Logo da Igreja'},
                {'nome': 'DEPARTAMENTO_LOGO', 'label': 'Logo do Departamento'},
                {'nome': 'NOME_DEPARTAMENTO', 'label': 'Nome do Departamento'},
                {'nome': 'COMPETENCIA', 'label': 'Mês/Ano'},
                {'nome': 'IGREJA_NOME', 'label': 'Nome da Igreja'},
                {'nome': 'IGREJA_CNPJ', 'label': 'CNPJ da Igreja'},
                {'nome': 'ESCALA_TABELA_HTML', 'label': 'Tabela de Escalas (Gerada pelo Sistema)'}
            ]
        }
    )
    print(" - Template PDF Escala criado.")

    # 2. Email Boas Vindas
    criar_template_email(
        'email_boas_vindas', 'E-mail: Bem-vindo à Intranet', 'Enviado quando o cadastro é aprovado',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'SENHA_TEMPORARIA', 'label': 'Senha'}, {'nome': 'LINK_LOGIN', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Seu cadastro foi aprovado! Agora você faz parte do sistema oficial da <strong>{{IGREJA_NOME}}</strong>.</p>
        <p>Para o seu primeiro acesso, utilize a seguinte senha temporária:</p>
        <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px; font-size: 18px; font-family: monospace; font-weight: bold; text-align: center;">
            {{SENHA_TEMPORARIA}}
        </div>
        <p>Recomendamos que você altere esta senha assim que fizer o primeiro login.</p>
        <center>
            <a href="{{LINK_LOGIN}}" style="display: inline-block; background-color: #1e40af; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Acessar o Sistema</a>
        </center>
        """
    )
    
    # 3. Escala Atualizada
    criar_template_email(
        'email_escala_atualizada', 'E-mail: Escala Atualizada', 'Enviado quando o líder altera uma escala',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOME_DEPARTAMENTO', 'label': 'Departamento'}, {'nome': 'LINK_PAINEL', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Informamos que o líder responsável acaba de publicar uma <strong>atualização na escala oficial</strong> do departamento <strong>{{NOME_DEPARTAMENTO}}</strong>.</p>
        <p>Por favor, acesse o sistema para conferir as alterações e garantir que você não perca o seu horário.</p>
        <center>
            <a href="{{LINK_PAINEL}}" style="display: inline-block; background-color: #eab308; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Ver Minha Escala</a>
        </center>
        """
    )

    # 4. Cancelamento de Escala (Líder cancela um voluntário específico)
    criar_template_email(
        'email_cancelamento_escala', 'E-mail: Você foi removido da Escala', 'Aviso de remoção',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOME_DEPARTAMENTO', 'label': 'Departamento'}, {'nome': 'DATA_HORA', 'label': 'Data do Culto'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Sua participação na escala do departamento <strong>{{NOME_DEPARTAMENTO}}</strong> no dia <strong>{{DATA_HORA}}</strong> foi cancelada pelo líder.</p>
        <p>Se você tiver alguma dúvida, entre em contato diretamente com a liderança do seu departamento.</p>
        """
    )

    # 5. Escala Cancelada (Culto inteiro cancelado)
    criar_template_email(
        'email_escala_cancelada', 'E-mail: Culto/Evento Cancelado', 'Aviso de culto cancelado',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOME_DEPARTAMENTO', 'label': 'Departamento'}, {'nome': 'DATA_HORA', 'label': 'Data do Culto'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Atenção! A programação do departamento <strong>{{NOME_DEPARTAMENTO}}</strong> agendada para o dia <strong>{{DATA_HORA}}</strong> foi <strong>cancelada</strong>.</p>
        <p>Consequentemente, todas as escalas para este dia também estão suspensas.</p>
        """
    )

    # 6. Nova Escala (Primeira vez que a competência é publicada)
    criar_template_email(
        'email_nova_escala', 'E-mail: Nova Escala Publicada', 'Aviso de publicação de mês',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOME_DEPARTAMENTO', 'label': 'Departamento'}, {'nome': 'COMPETENCIA', 'label': 'Mês/Ano'}, {'nome': 'LINK_PAINEL', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>A escala oficial do departamento <strong>{{NOME_DEPARTAMENTO}}</strong> para o mês de <strong>{{COMPETENCIA}}</strong> acabou de ser publicada!</p>
        <p>Acesse a Intranet agora mesmo para verificar em quais dias você está escalado e se programe com antecedência.</p>
        <center>
            <a href="{{LINK_PAINEL}}" style="display: inline-block; background-color: #16a34a; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Conferir Minha Escala</a>
        </center>
        """
    )

    # 7. Novo Aviso (Mural)
    criar_template_email(
        'email_novo_aviso', 'E-mail: Novo Aviso no Mural', 'Aviso do líder para a equipe',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOME_DEPARTAMENTO', 'label': 'Departamento'}, {'nome': 'TITULO_AVISO', 'label': 'Título'}, {'nome': 'CONTEUDO_AVISO', 'label': 'Conteúdo'}, {'nome': 'LINK_PAINEL', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>A liderança do departamento <strong>{{NOME_DEPARTAMENTO}}</strong> publicou um novo recado importante no mural:</p>
        <div style="background-color: #f8fafc; border-left: 4px solid #1e40af; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #1e3a8a;">{{TITULO_AVISO}}</h3>
            <p style="white-space: pre-wrap; font-size: 14px; margin-bottom: 0;">{{CONTEUDO_AVISO}}</p>
        </div>
        <center>
            <a href="{{LINK_PAINEL}}" style="display: inline-block; background-color: #1e40af; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Acessar o Painel</a>
        </center>
        """
    )

    # 8. Promoção Hierárquica
    criar_template_email(
        'email_promocao_hierarquica', 'E-mail: Você foi Promovido!', 'Mudança de nível no sistema',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'NOVO_NIVEL', 'label': 'Nível'}, {'nome': 'LINK_SISTEMA', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Temos uma excelente notícia! Seu nível de acesso na Intranet foi atualizado.</p>
        <p>Você agora possui as permissões de: <strong>{{NOVO_NIVEL}}</strong>.</p>
        <p>Acesse o sistema para conferir suas novas funcionalidades e módulos liberados.</p>
        <center>
            <a href="{{LINK_SISTEMA}}" style="display: inline-block; background-color: #1e40af; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Acessar a Intranet</a>
        </center>
        """
    )

    # 9. Termo LGPD (Assinatura do Termo Geral de Uso)
    criar_template_email(
        'email_termo_lgpd', 'E-mail: Solicitação de Aceite - LGPD', 'Aviso para assinar termo',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'TITULO_TERMO', 'label': 'Título'}, {'nome': 'LINK_SISTEMA', 'label': 'Link'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        <p>Um novo termo legal (<strong>{{TITULO_TERMO}}</strong>) foi publicado pela administração da Igreja e exige a sua leitura e consentimento.</p>
        <p>Para continuar utilizando o sistema normalmente, pedimos que acesse a plataforma e registre a sua ciência digital.</p>
        <center>
            <a href="{{LINK_SISTEMA}}" style="display: inline-block; background-color: #dc2626; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin-top: 20px;">Ler e Assinar Termo</a>
        </center>
        """
    )

    # 10. Genérico
    criar_template_email(
        'email_generico', 'E-mail: Mensagem do Sistema', 'E-mail livre e genérico',
        [{'nome': 'NOME', 'label': 'Nome'}, {'nome': 'MENSAGEM_HTML', 'label': 'Mensagem Livre (HTML)'}],
        """
        <p>Olá, <strong>{{NOME}}</strong>,</p>
        {{MENSAGEM_HTML}}
        """
    )
    
    print("Concluído!")

if __name__ == '__main__':
    run()
