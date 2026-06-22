"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/ai_auto_engineer.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
"""
import os
import sys
import datetime
import re
import json
import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.models import SpiderTestLog, AIEngineerLog
from intranet.services.gemini_ai import consultar_gemini_json
from django.conf import settings

class Command(BaseCommand):
    help = 'IA Autônoma: Roda testes, identifica bugs, programa correções, testa e aplica via Git (ou faz Rollback)'

    def add_arguments(self, parser):
        parser.add_argument('--target_log_id', type=int, help='ID of the AIEngineerLog to process')

    def registrar_falha(self, log_registro, status, detalhes):
        if log_registro:
            log_registro.status = status
            log_registro.detalhes += f"\n{detalhes}"
            log_registro.save()

            subject = f"BUG persistente encontrado: {status}"
            message = f"Eversinho falhou ao consertar um bug.\nStatus: {status}\n\nDetalhes do Erro:\n{log_registro.erro_analisado}\n\nDetalhes da Falha:\n{detalhes}"

            self.stderr.write("==================================================")
            self.stderr.write(f"📧 [EMAIL SIMULADO ENVIADO AO DEV] 📧")
            self.stderr.write(f"Para: marcos@pvenseada.org")
            self.stderr.write(f"Assunto: {subject}")
            self.stderr.write(f"Mensagem:\n{message}")
            self.stderr.write("==================================================")

            try:
                from intranet.services.gmail_service import enviar_email_simples
                enviar_email_simples(
                    destinatario='marcos@pvenseada.org',
                    assunto=subject,
                    corpo=message
                )
            except Exception as e:
                self.stderr.write(f"Falha ao enviar email real via SMTP: {str(e)}")

    def handle(self, *args, **options):
        self.stdout.write("==================================================")
        self.stdout.write("[AI] MOTOR DE IA AUTÔNOMA INICIADO (AI AUTO-ENGINEER)")
        self.stdout.write("==================================================")

        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            self.stderr.write("Erro: API Key do Google Gemini não configurada. Impossível operar.")
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
                self.stdout.write("[OK] Sistema 100% íntegro. A IA não encontrou trabalho para fazer.")
                return

            import re
            erros_blocos = []
            linhas = spider_log.log_texto.split('\n')
            bloco_atual = []
            capturando = False
            for linha in linhas:
                if any(x in linha for x in ['[ERROR', '[SECURITY ERROR]', '[EXCEPTION]']):
                    if bloco_atual:
                        erros_blocos.append('\n'.join(bloco_atual))
                    bloco_atual = [linha]
                    capturando = True
                elif capturando and linha.startswith('['):
                    if bloco_atual:
                        erros_blocos.append('\n'.join(bloco_atual))
                        bloco_atual = []
                    capturando = False
                elif capturando:
                    bloco_atual.append(linha)

            if bloco_atual:
                erros_blocos.append('\n'.join(bloco_atual))

            if not erros_blocos:
                self.stdout.write("Nenhum bloco de erro decifrável no log do spider.")
                return

            alvo_erro = next((b for b in erros_blocos if '[EXCEPTION]' in b), erros_blocos[0])
            # Cria o registro pendente pra dar sequencia no fluxo padrao
            log_registro = AIEngineerLog.objects.create(erro_analisado=alvo_erro, status='PROCESSANDO', detalhes=alvo_erro)

        self.stdout.write(f"[ALVO] Erro Alvo Escolhido: {alvo_erro[:100]}...")

        # 3. Engenharia de IA (Prompt e Correção)
        self.stdout.write("[3/5] Consultando Inteligência Artificial (Google Gemini 2.5 Flash) para programar a solução...")

        import re
        arquivos_contexto = ""
        matches = re.findall(r'File "([^"]+\.py)", line (\d+)', alvo_erro)
        base_dir = settings.BASE_DIR
        for c, linha_str in matches:
            if 'venv' not in c and os.path.exists(c):
                linha = int(linha_str)
                try:
                    rel_path = os.path.relpath(c, base_dir)
                    with open(c, 'r', encoding='utf-8') as f:
                        linhas_arq = f.readlines()
                        start = max(0, linha - 30)
                        end = min(len(linhas_arq), linha + 30)
                        trecho = "".join(linhas_arq[start:end])
                        arquivos_contexto += f"\n\n--- TRECHO DO ARQUIVO {rel_path} (linhas {start+1} a {end}) ---\n{trecho}\n"
                except Exception:
                    pass

        # === LÓGICA DO CÉREBRO: LER HISTÓRICO DE ERROS ===
        cerebro_historico_dir = os.path.join(base_dir, 'docs', 'meu_cerebro', 'ai_daemon')
        os.makedirs(cerebro_historico_dir, exist_ok=True)

        historico_cerebro = ""
        try:
            # Pega os 5 arquivos mais recentes de erros
            arquivos_hist = [os.path.join(cerebro_historico_dir, f) for f in os.listdir(cerebro_historico_dir) if f.endswith('.md')]
            arquivos_hist.sort(key=os.path.getmtime, reverse=True)
            recentes = arquivos_hist[:5]

            for arq in recentes:
                if arq.endswith('LESSONS.md'): continue
                with open(arq, 'r', encoding='utf-8') as f:
                    historico_cerebro += f"\n\n--- HISTÓRICO DE ERRO: {os.path.basename(arq)} ---\n{f.read()}\n"
        except Exception as e:
            self.stderr.write(f"Erro ao ler o histórico de erros da IA: {e}")

        # === MEMÓRIA DE LONGO PRAZO (LESSONS.md) ===
        lessons_path = os.path.join(cerebro_historico_dir, 'LESSONS.md')
        if os.path.exists(lessons_path):
            with open(lessons_path, 'r', encoding='utf-8') as f:
                historico_cerebro += f"\n\n--- LIÇÕES APRENDIDAS (MEMÓRIA CONTÍNUA) ---\n{f.read()}\n"

        # === LÓGICA DO CÉREBRO: LER BASE DE CONHECIMENTO (RAG COM CACHE) ===
        from django.core.cache import cache
        knowledge = cache.get('eversinho_rag_knowledge')

        if not knowledge:
            cerebro_conhecimento_dir = os.path.join(base_dir, 'docs', 'meu_cerebro')
            knowledge = ''
            try:
                # Lê todos os arquivos MD diretamente na raiz do meu_cerebro (ignora subpastas)
                if os.path.exists(cerebro_conhecimento_dir):
                    arquivos_conhecimento = [
                        f for f in os.listdir(cerebro_conhecimento_dir)
                        if f.endswith('.md') and os.path.isfile(os.path.join(cerebro_conhecimento_dir, f))
                    ]
                    for arq in arquivos_conhecimento:
                        caminho_arq = os.path.join(cerebro_conhecimento_dir, arq)
                        with open(caminho_arq, 'r', encoding='utf-8') as kf:
                            knowledge += f"\n\n--- DOCUMENTAÇÃO BASE: {arq} ---\n{kf.read()}\n"
            except Exception as e:
                self.stderr.write(f"Erro ao ler a base de conhecimento RAG da IA: {e}")

            knowledge_base_path = os.path.join(base_dir, 'eversinho_knowledge.txt')
            if os.path.exists(knowledge_base_path):
                with open(knowledge_base_path, 'r', encoding='utf-8') as kf:
                    knowledge += f"\n\n--- REGRAS LEGADAS (eversinho_knowledge.txt) ---\n{kf.read()}\n"

            cache.set('eversinho_rag_knowledge', knowledge, 86400)

        prompt = f"""
        Você é a IA Autônoma (Engenheiro de Software) da Intranet PVE desenvolvida em Django.

        [=== BASE DE CONHECIMENTO RECENTE ===]
        {knowledge}
        [====================================]

        Um erro foi detectado pelos testes:

        ERRO DETECTADO:
        {alvo_erro}

        Abaixo estão os trechos dos arquivos onde o erro ocorreu:
        {arquivos_contexto}

        HISTÓRICO RECENTE DO SEU CÉREBRO (O QUE VOCÊ JÁ FEZ):
        Use este histórico para não cometer os mesmos erros ou desfazer algo que você já consertou.
        {historico_cerebro}

        REGRAS:
        1. Analise o traceback. Descubra qual arquivo causou o problema.
        2. OU se você perceber que o erro não é do sistema, mas sim uma falha no próprio robô Spider de testes, aprimore o spider.

        Forneça EXATAMENTE um JSON com as alterações sugeridas. O JSON deve ter este formato rigoroso:
        {{
            "target_file": "caminho/do/arquivo.py",
            "search_content": "código exato atual com problema para ser substituído",
            "replace_content": "código novo corrigido",
            "aprendizado": "Frase curta descrevendo o que você aprendeu com este erro para sua memória contínua."
        }}
        Importante: não retorne NADA ALÉM do JSON válido.
        O search_content DEVE ser uma cópia EXATA, caractere por caractere.
        """

        try:
            texto_limpo = consultar_gemini_json(prompt)
            texto_limpo = texto_limpo.replace('```json', '').replace('```', '').strip()

            acao = json.loads(texto_limpo)
            target_file = acao.get("target_file", "").lstrip('/')
            search_content = acao.get("search_content", "")
            replace_content = acao.get("replace_content", "")
            aprendizado_ia = acao.get("aprendizado", "Bug corrigido sem resumo.")

            # TRAVA DE SEGURANÇA (LIMITAÇÕES DE ESCOPO MÁXIMO)
            arquivos_proibidos = ['settings.py', 'wsgi.py', 'asgi.py', 'manage.py']
            if any(proibido in target_file for proibido in arquivos_proibidos) or '..' in target_file:
                self.stderr.write(f"Violacão de Segurança: IA tentou modificar um arquivo crítico ({target_file}). Abortando.")
                self.registrar_falha(log_registro, 'FALHA_DE_SEGURANCA', f"Tentativa de alteração em {target_file}")
                return

            if not os.path.exists(target_file):
                self.stderr.write(f"A IA propôs alterar {target_file}, mas o arquivo não existe.")
                self.registrar_falha(log_registro, 'FALHA_NA_GERACAO', f"Arquivo {target_file} não encontrado.")
                return

            self.stdout.write(f"[4/5] Aplicando Código Proposto no arquivo: {target_file}")

            # Lê e substitui o código
            with open(target_file, 'r', encoding='utf-8') as f:
                conteudo_original = f.read()

            if search_content not in conteudo_original:
                self.stderr.write("O conteúdo de busca gerado pela IA não foi encontrado no arquivo exato.")
                self.stderr.write(f"Search content gerado: {repr(search_content)}")
                self.registrar_falha(log_registro, 'ERRO_BUSCA_CODIGO', f"Search block not found in {target_file}")
                return

            conteudo_novo = conteudo_original.replace(search_content, replace_content)

            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(conteudo_novo)

            # === VALIDAÇÃO SINTÁTICA IMEDIATA ===
            if target_file.endswith('.py'):
                import py_compile
                try:
                    py_compile.compile(target_file, doraise=True)
                except py_compile.PyCompileError as syntax_err:
                    self.stderr.write(f"Validação Sintática Falhou! A IA gerou código com SyntaxError.")
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(conteudo_original)
                    self.registrar_falha(log_registro, 'ERRO_SINTAXE', f"SyntaxError gerado pela IA. Rollback imediato.\n{str(syntax_err)}")
                    return

            # 4. Homologação (Rodar Spider Novamente)
            self.stdout.write("[5/5] Testando Modificação (Aguardando Hupper reiniciar o servidor)...")
            import time
            time.sleep(5)

            self.stdout.write("Rodando Spider Test em um novo processo isolado...")
            spider_antes = SpiderTestLog.objects.order_by('-data_execucao').first()
            id_antes = spider_antes.id if spider_antes else None

            resultado = subprocess.run([sys.executable, 'manage.py', 'run_spider'])

            spider_pos = SpiderTestLog.objects.order_by('-data_execucao').first()
            id_pos = spider_pos.id if spider_pos else None

            if resultado.returncode != 0 or id_antes == id_pos:
                erros_depois = 9999
                self.stderr.write("Spider crashou! Erro fatal de sintaxe introduzido.")
            else:
                erros_depois = spider_pos.erros_encontrados

            # 5. Avaliação Humana (Rollback ou Git)
            if erros_depois < erros_antes:
                self.stdout.write("[SUCCESS] SUCESSO! A IA corrigiu o bug e o sistema ficou mais íntegro.")
                log_registro.status = 'CORRIGIDO_HOMOLOGADO'
                log_registro.save()

                agora_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

                # SALVA A LIÇÃO NA MEMÓRIA DE LONGO PRAZO
                with open(lessons_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"- Em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}: Erro resolvido em `{target_file}`. Aprendizado: {aprendizado_ia}\n")

                relatorio_md = f"""# Relatório de Correção Autônoma ({agora_str})
## 1. Erro Detectado
```text
{alvo_erro}
```
## 2. Arquivo Alvo
{target_file}
## 3. O Que Tinha Antes
```python
{search_content}
```
## 4. O Que Foi Colocado
```python
{replace_content}
```
## 5. Resultado
A correção diminuiu o número de erros detectados pelo Spider de {erros_antes} para {erros_depois}. O sistema foi homologado com sucesso.
"""
                with open(os.path.join(cerebro_historico_dir, f"{agora_str}.md"), 'w', encoding='utf-8') as f:
                    f.write(relatorio_md)
            else:
                self.stdout.write("[FAIL] FALHA! A correção não resolveu o problema. Realizando Rollback...")
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(conteudo_original)
                subprocess.run(['git', 'restore', target_file])

                self.registrar_falha(log_registro, 'ROLLBACK', f"Erros não caíram ({erros_depois}). Rollback ativado. Arquivo ({target_file})")
                self.stdout.write("Rollback executado. O sistema voltou ao estado estável anterior.")

        except Exception as e:
            self.stderr.write(f"Falha Crítica no Motor de IA: {str(e)}")
            self.registrar_falha(log_registro, 'ERRO_SISTEMA', str(e))
