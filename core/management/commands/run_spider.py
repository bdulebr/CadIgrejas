"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/run_spider.py
* DESCRIÇÃO: Motor de Varredura E2E (Auditoria de Rotas e Integridade de Banco de Dados)
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 4.0.0
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026
"""
import re
import time
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import get_resolver
from django.conf import settings
from django.apps import apps
from django.db import connection
from core.models import Membro, SpiderTestLog

class Command(BaseCommand):
    help = 'Executa o spider test varrendo URLs (com fuzzing) e auditando todas as tabelas do banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=int, help='ID do usuário que acionou')

    def handle(self, *args, **options):
        settings.AXES_ENABLED = False
        client = Client()
        log_lines = []
        errors_found = 0

        self.stdout.write("Iniciando auditoria completa (Banco de Dados + Rotas)...")
        log_lines.append("=== INICIANDO AUDITORIA GLOBAL ===")

        # ==========================================
        # FASE 1: VARREDURA DE INTEGRIDADE DO BANCO
        # ==========================================
        log_lines.append("\n--- [FASE 1: DATABASE SCAN] ---")

        models = apps.get_models()
        total_tables = len(models)

        for model in models:
            table_name = model._meta.db_table
            try:
                # Tenta fazer uma contagem rápida para validar se a tabela existe e não está corrompida
                count = model.objects.count()

                # Tenta buscar o primeiro e último registro para validar integridade das colunas
                primeiro = model.objects.first()

                log_lines.append(f"[DB OK] Tabela {table_name} acessível. Registros: {count}")
            except Exception as e:
                errors_found += 1
                log_lines.append(f"[DB ERROR] Falha crítica na tabela {table_name}: {str(e)}")

        # ==========================================
        # FASE 2: PREPARAÇÃO DE SESSÃO E AUTH API
        # ==========================================
        try:
            user = Membro.objects.get(username='admin_spider')
        except Membro.DoesNotExist:
            user = Membro.objects.create_superuser(
                username='admin_spider',
                email='spider@teste.com',
                password='password123',
                cpf='99999999999',
                nivel_hierarquico='super_admin'
            )

        client.login(username='admin_spider', password='password123')

        try:
            res_auth = client.post('/api/auth/login/', {'username': 'admin_spider', 'password': 'password123'}, content_type='application/json')
            if res_auth.status_code == 200:
                jwt_token = res_auth.json().get('access')
        except Exception:
            pass

        # ==========================================
        # FASE 3: VARREDURA E FUZZING DE ROTAS
        # ==========================================
        log_lines.append("\n--- [FASE 2: ROUTE SCAN & FUZZING] ---")

        resolver = get_resolver()

        def get_all_urls(urllist, prefix=''):
            all_urls = []
            for entry in urllist:
                if hasattr(entry, 'url_patterns'):
                    all_urls.extend(get_all_urls(entry.url_patterns, prefix + str(entry.pattern)))
                else:
                    all_urls.append(prefix + str(entry.pattern))
            return all_urls

        urls = get_all_urls(resolver.url_patterns)
        processed_urls = set()

        for url in urls:
            if any(x in url for x in ['admin/', 'media', 'qr/', 'logout', 'run-spider']):
                continue

            clean_url = '/' + url.replace('^', '').replace('$', '').replace('\\Z', '')

            # Fuzzing de parâmetros: em vez de ignorar rotas com IDs, injetamos dados de teste genéricos
            clean_url = re.sub(r'<int:\w+>', '1', clean_url)
            clean_url = re.sub(r'<uuid:\w+>', '00000000-0000-0000-0000-000000000000', clean_url)
            clean_url = re.sub(r'<slug:\w+>', 'teste-qa', clean_url)
            clean_url = re.sub(r'<str:\w+>', 'teste-str', clean_url)

            # Se a rota foi totalmente resolvida e não tem mais marcações de regex, adiciona pra varredura
            if '<' not in clean_url and '(' not in clean_url:
                processed_urls.add(clean_url)

        total_urls = len(processed_urls)

        for path in processed_urls:
            start_time = time.time()
            try:
                response = client.get(path)
                exec_time = round((time.time() - start_time) * 1000) # tempo em ms

                if response.status_code >= 500:
                    log_lines.append(f"[ERROR {response.status_code}] {path} ({exec_time}ms)")
                    errors_found += 1
                elif response.status_code == 404:
                    log_lines.append(f"[WARNING 404] {path} (Not Found)")
                else:
                    # Registra endpoints lentos sem quebrar o teste
                    if exec_time > 1500:
                        log_lines.append(f"[OK {response.status_code}] {path} - GARGALO DE REDE: {exec_time}ms")
                    else:
                        log_lines.append(f"[OK {response.status_code}] {path} ({exec_time}ms)")

            except Exception as e:
                log_lines.append(f"[EXCEPTION] {path} -> {e}")
                errors_found += 1

        # ==========================================
        # FASE 3: AUDITORIA E CORREÇÃO VIA IA
        # ==========================================
        log_lines.append("\n--- [FASE 3: AI AUTO-FIX / ANOMALIA SCAN] ---")
        self.stdout.write("\nIniciando Motor de Automação de IA (Auditoria Geral)...")
        try:
            from django.core.management import call_command
            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = saida_ia = io.StringIO()

            call_command('ai_auto_fix')

            sys.stdout = old_stdout
            texto_saida_ia = saida_ia.getvalue()

            for linha in texto_saida_ia.split('\n'):
                if linha.strip():
                    log_lines.append(f"[AI] {linha.strip()}")
                    self.stdout.write(f"[AI] {linha.strip()}")

        except Exception as e:
            log_lines.append(f"[EXCEPTION AI] Erro ao executar motor IA: {e}")
            self.stderr.write(f"Erro ao executar AI Auto-Fix: {e}")

        # ==========================================
        # FINALIZAÇÃO E REGISTRO
        # ==========================================
        resumo = f"\n[SPIDER COMPLETE] {errors_found} errors found in {total_tables} DB tables and {total_urls} endpoints scanned."
        log_lines.append(resumo)
        self.stdout.write(resumo)

        user_acionador = Membro.objects.filter(id=options.get('user_id')).first() if options.get('user_id') else None

        SpiderTestLog.objects.create(
            iniciado_por=user_acionador,
            total_urls=total_urls,
            erros_encontrados=errors_found,
            log_texto="\n".join(log_lines)
        )
