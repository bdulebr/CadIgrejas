"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/management/commands/run_spider.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
import json
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import get_resolver
from django.conf import settings
from core.models import Membro, SpiderTestLog

class Command(BaseCommand):
    help = 'Executa o spider test (E2E) varrendo todas as URLs locais e logando no banco'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=int, help='ID do usuário que acionou')

    def handle(self, *args, **options):
        # Desabilita Axes para evitar lockout
        settings.AXES_ENABLED = False
        client = Client()

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

        # Autenticação JWT para API
        jwt_token = None
        try:
            res_auth = client.post('/api/auth/login/', {'username': 'admin_spider', 'password': 'password123'}, content_type='application/json')
            if res_auth.status_code == 200:
                jwt_token = res_auth.json().get('access')
        except Exception as e:
            pass


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

        errors_found = 0
        log_lines = []
        total_urls = 0

        for url in set(urls):
            if 'admin/' in url or '<' in url or 'media' in url or 'qr/' in url or 'logout' in url or 'run-spider' in url:
                continue

            path = '/' + url.replace('^', '').replace('$', '').replace('\\Z', '')
            total_urls += 1

            try:
                response = client.get(path)
                if response.status_code == 500:
                    log_lines.append(f"[ERROR 500] {path}")
                    errors_found += 1
                elif response.status_code == 404:
                    pass
                else:
                    log_lines.append(f"[OK {response.status_code}] {path}")
            except Exception as e:
                log_lines.append(f"[EXCEPTION] {path} -> {e}")
                errors_found += 1

        resumo = f"\n[SPIDER COMPLETE] {errors_found} errors found in {total_urls} scanned endpoints."
        log_lines.append(resumo)
        self.stdout.write(resumo)

        # Log no Banco
        user_acionador = None
        user_id = options.get('user_id')
        if user_id:
            user_acionador = Membro.objects.filter(id=user_id).first()

        SpiderTestLog.objects.create(
            iniciado_por=user_acionador,
            total_urls=total_urls,
            erros_encontrados=errors_found,
            log_texto="\n".join(log_lines)
        )
