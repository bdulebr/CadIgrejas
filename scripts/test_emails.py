"""
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: scripts/test_emails.py
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
"""
import os
import django

# Configurar o Django para rodar scripts avulsos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intranet.settings')
django.setup()

from intranet.services.gmail_service import enviar_email_html

destinatario = "marcosgja93@gmail.com"
print(f"Iniciando disparos de teste para {destinatario}...")

# 1. Boas Vindas
print("Enviando Boas Vindas...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Bem-vindo!", "boas_vindas.html", {
    "nome": "Marcos Lira",
    "email_login": destinatario,
    "senha": "senha-temporaria-123",
    "link_login": "http://localhost:8000/login"
})

# 2. Nova Escala
print("Enviando Nova Escala...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Nova Escala Publicada", "nova_escala.html", {
    "departamento": "Mídia & Tecnologia",
    "nome": "Marcos Lira",
    "data": "14/06/2026 (Domingo)",
    "horario_inicio": "09:00",
    "horario_fim": "12:00",
    "funcao": "Câmera Principal",
    "link_painel": "http://localhost:8000/minhas-escalas"
})

# 3. Escala Atualizada
print("Enviando Escala Atualizada...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Escala Atualizada", "escala_atualizada.html", {
    "nome": "Marcos Lira",
    "departamento": "Mídia & Tecnologia",
    "link_painel": "http://localhost:8000/minhas-escalas"
})

# 4. Escala Cancelada
print("Enviando Escala Cancelada...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Cancelamento de Escala", "escala_cancelada.html", {
    "nome": "Marcos Lira",
    "departamento": "Mídia & Tecnologia",
    "data": "14/06/2026",
    "horario_inicio": "09:00",
    "horario_fim": "12:00",
    "link_painel": "http://localhost:8000/minhas-escalas"
})

# 5. Termo LGPD
print("Enviando LGPD...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Assinatura Eletrônica LGPD", "termo_lgpd.html", {
    "solicitante": "Administração PV Enseada",
    "link_assinatura": "http://localhost:8000/midia/lgpd/assinatura/teste123"
})

# 6. Novo Aviso
print("Enviando Aviso...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Novo Aviso no Mural", "novo_aviso.html", {
    "aviso_titulo": "Reunião Geral de Liderança",
    "aviso_conteudo": "Líderes, teremos um encontro muito importante no próximo sábado às 15:00 na sala anexa. Não faltem!",
    "link_painel": "http://localhost:8000/dashboard"
})

# 7. Promoção Hierárquica
print("Enviando Promoção...")
enviar_email_html(destinatario, "[Teste Intranet PVE] Você foi promovido!", "promocao_hierarquica.html", {
    "nome": "Marcos Lira",
    "novo_nivel": "Líder de Departamento",
    "link_painel": "http://localhost:8000/dashboard"
})

print("=============================")
print("TODOS OS TESTES DISPARADOS!")
