import os
import sys

def migrar():
    print("--- INICIANDO MIGRAÇÃO DE DADOS (SQLite -> PostgreSQL) ---")
    
    # 1. Gerar o dump do SQLite ignorando tabelas problemáticas
    print("1. Gerando snapshot de dados do SQLite (datadump.json)...")
    res = os.system("python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 4 > datadump.json")
    if res != 0:
        print("Erro ao gerar o dump de dados. Cancele e verifique.")
        sys.exit(1)
        
    print("Snapshot criado com sucesso.")
    print("\n--- ATENÇÃO ---")
    print("Agora você deve mudar o seu arquivo .env para apontar para o PostgreSQL:")
    print("DATABASE_URL=postgres://erp_admin:PVE@MasterDB2026!@localhost:5432/intranet_pve")
    print("\nApós fazer a mudança no .env, pressione ENTER para continuar a injeção de dados no PostgreSQL...")
    input()
    
    print("2. Aplicando migrações estruturais no PostgreSQL...")
    res = os.system("python manage.py migrate")
    if res != 0:
        print("Erro ao aplicar migrações no PostgreSQL.")
        sys.exit(1)
        
    print("3. Injetando dados (loaddata)...")
    res = os.system("python manage.py loaddata datadump.json")
    if res != 0:
        print("Erro ao carregar dados no PostgreSQL. Tente limpar tabelas se houve conflito.")
        sys.exit(1)
        
    print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("Pode apagar o arquivo datadump.json por segurança.")

if __name__ == "__main__":
    migrar()
