import os
import re
import json
import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.models import SpiderTestLog, AIEngineerLog
from intranet.services.groq_ai import obter_client_groq

class Command(BaseCommand):
    help = 'IA Autônoma: Roda testes, identifica bugs, programa correções, testa e aplica via Git (ou faz Rollback)'

    def add_arguments(self, parser):
        parser.add_argument('--target_log_id', type=int, help='ID of the AIEngineerLog to process')

    def handle(self, *args, **options):
        self.stdout.write("==================================================")
        self.stdout.write("🤖 MOTOR DE IA AUTÔNOMA INICIADO (AI AUTO-ENGINEER)")
        self.stdout.write("==================================================")

        client = obter_client_groq()
        if not client:
            self.stderr.write("Erro: API Key do Groq não configurada. Impossível operar.")
            return

        target_log_id = options.get('target_log_id')
        log_registro = None
        alvo_erro = ""

        if target_log_id:
            # Acionado pelo Daemon a partir de um Erro 500
            self.stdout.write(f"[1/5] Lendo Bug do Cão de Guarda (Log ID {target_log_id})...")
            log_registro = AIEngineerLog.objects.filter(id=target_log_id).first()
            if not log_registro:
                self.stderr.write("Log não encontrado.")
                return
            alvo_erro = log_registro.detalhes
            erros_antes = 1 # O erro atual conta como 1
        else:
            # Acionado manualmente pelo painel SysAdmin
            self.stdout.write("[1/5] Executando Auditoria Completa do Spider...")
            try:
                call_command('run_spider')
            except Exception as e:
                self.stderr.write(f"Falha ao rodar o spider internamente: {e}")

            spider_log = SpiderTestLog.objects.order_by('-data_execucao').first()
            if not spider_log:
                self.stderr.write("Nenhum log do Spider encontrado.")
                return

            erros_antes = spider_log.erros_encontrados
            self.stdout.write(f"[2/5] Análise do Spider: {erros_antes} erros detectados.")

            if erros_antes == 0:
                self.stdout.write("🎉 Sistema 100% íntegro. A IA não encontrou trabalho para fazer.")
                return

            linhas_erro = [linha for linha in spider_log.log_texto.split('\n') if '[ERROR' in linha or '[SECURITY ERROR]' in linha]
            if not linhas_erro:
                self.stdout.write("Nenhuma linha de erro decifrável no log do spider.")
                return

            alvo_erro = linhas_erro[0]
            # Cria o registro pendente pra dar sequencia no fluxo padrao
            log_registro = AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='PROCESSANDO', detalhes=alvo_erro)

        self.stdout.write(f"🛑 Erro Alvo Escolhido: {alvo_erro[:100]}...")

        # 3. Engenharia de IA (Prompt e Correção)
        self.stdout.write("[3/5] Consultando Inteligência Artificial (Groq Llama-3) para programar a solução...")

        # Tentar adivinhar qual arquivo afeta (um mapeamento raso pra IA focar, geralmente urls.py ou views.py)
        # Vamos passar os arquivos principais para a IA se ela pedir, ou mandar o conteudo de views e urls.
        # Por limitações de token, passamos a estrutura ou pedimos sugestões puras.

        prompt = f"""
        Você é a IA Autônoma (Engenheiro de Software) da Intranet PVE desenvolvida em Django.
        Durante a execução dos testes E2E automáticos, encontramos o seguinte erro em produção:

        ERRO DETECTADO:
        {alvo_erro}

        Seu objetivo:
        1. Descubra qual arquivo Python ou HTML no sistema deve ser corrigido para consertar esse erro.
        2. OU se você perceber que o erro não é do sistema, mas sim uma falha no próprio robô Spider de testes (falso positivo, ou falta de uma trava), você PODE E DEVE aprimorar o código do spider (em 'core/management/commands/run_spider.py').

        Regra de Segurança Estrita: Você só tem permissão para modificar arquivos dentro das pastas dos apps de negócio (core/, almoxarifado/, escalas/, tesouraria/, etc.). NUNCA modifique settings.py, wsgi.py, asgi.py ou manage.py.

        Forneça EXATAMENTE um JSON com as alterações sugeridas. O JSON deve ter este formato rigoroso:
        {{
            "target_file": "caminho/do/arquivo.py",
            "search_content": "código exato atual com problema para ser substituído",
            "replace_content": "código novo corrigido"
        }}
        Importante: não retorne NADA ALÉM do JSON válido, sem tags ```json. O arquivo_target deve ser o caminho relativo, ex: core/views.py.
        O search_content deve ser um trecho preciso de código (evite arquivos inteiros).
        """

        try:
            response = client.models.generate_content(
                model='llama-3.3-70b-versatile',
                contents=[prompt]
            )

            texto_limpo = response.text.replace('```json', '').replace('```', '').strip()

            # Se a IA não conseguir gerar JSON válido, vai pro except e aborta a operação segura
            acao = json.loads(texto_limpo)
            target_file = acao.get("target_file", "").lstrip('/')
            search_content = acao.get("search_content", "")
            replace_content = acao.get("replace_content", "")

            # TRAVA DE SEGURANÇA (LIMITAÇÕES DE ESCOPO MÁXIMO)
            arquivos_proibidos = ['settings.py', 'wsgi.py', 'asgi.py', 'manage.py']
            if any(proibido in target_file for proibido in arquivos_proibidos) or '..' in target_file:
                self.stderr.write(f"Violacão de Segurança: IA tentou modificar um arquivo crítico ({target_file}). Abortando.")
                AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='FALHA_DE_SEGURANCA', detalhes=f"Tentativa de alteração em {target_file}")
                return

            if not os.path.exists(target_file):
                self.stderr.write(f"A IA propôs alterar {target_file}, mas o arquivo não existe.")
                AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='FALHA_NA_GERACAO', detalhes=f"Arquivo {target_file} não encontrado.")
                return

            self.stdout.write(f"[4/5] Aplicando Código Proposto no arquivo: {target_file}")

            # Lê e substitui o código
            with open(target_file, 'r', encoding='utf-8') as f:
                conteudo_original = f.read()

            if search_content not in conteudo_original:
                self.stderr.write("O conteúdo de busca gerado pela IA não foi encontrado no arquivo exato.")
                AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='ERRO_BUSCA_CODIGO', detalhes=f"Search block not found in {target_file}")
                return

            conteudo_novo = conteudo_original.replace(search_content, replace_content)

            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(conteudo_novo)

            # 4. Homologação (Rodar Spider Novamente)
            self.stdout.write("[5/5] Testando Modificação (Aguardando Hupper reiniciar o servidor)...")
            # Espera 5 segundos para o Hupper reiniciar o Waitress com o novo código
            import time
            time.sleep(5)

            self.stdout.write("Rodando Spider Test em um novo processo isolado...")
            import sys
            subprocess.run([sys.executable, 'manage.py', 'run_spider'])

            spider_pos = SpiderTestLog.objects.order_by('-data_execucao').first()
            erros_depois = spider_pos.erros_encontrados if spider_pos else erros_antes

            # 5. Avaliação Humana (Rollback ou Git)
            if erros_depois < erros_antes:
                # O Erro diminuiu, a correção funcionou!
                self.stdout.write("✅ SUCESSO! A IA corrigiu o bug e o sistema ficou mais íntegro.")
                AIEngineerLog.objects.create(erro_analisado=alvo_erro, arquivo_modificado=target_file, status='SUCESSO', detalhes=f"Erros caíram de {erros_antes} para {erros_depois}.")

                # Consolida via Git (Adiciona mas o commit final fica a cargo do Dev)
                subprocess.run(['git', 'add', target_file])
                self.stdout.write("As mudanças foram adicionadas ao Git e estão seguras.")
            else:
                # O Erro continuou ou piorou! ROLLBACK!
                self.stderr.write("❌ FALHA! A correção piorou ou não resolveu. Iniciando Rollback de Segurança...")

                # Volta o código original
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(conteudo_original)

                # Ou usa Git diretamente para ter 100% de precisão de rollback no repo
                subprocess.run(['git', 'restore', target_file])

                AIEngineerLog.objects.create(erro_analisado=alvo_erro, arquivo_modificado=target_file, status='ROLLBACK', detalhes=f"Erros não caíram ({erros_depois}). Rollback ativado.")
                self.stdout.write("Rollback executado. O sistema voltou ao estado estável anterior.")

        except Exception as e:
            self.stderr.write(f"Falha Crítica no Motor de IA: {str(e)}")
            AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='ERRO_SISTEMA', detalhes=str(e))
