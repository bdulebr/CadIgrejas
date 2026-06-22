with open("core/templates/core/pages/sysadmin_dashboard.html", "r", encoding="utf-8") as f:
    content = f.read()

# Patch 1: Baixar Backup Atual
old_link_1 = """                                    <a href="{% url 'sysadmin_baixar_backup' %}" class="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded transition-colors" title="Baixar DB Atual">
                                        <i data-lucide="download" class="w-4 h-4"></i>
                                    </a>"""

new_form_1 = """                                    <form method="POST" action="{% url 'sysadmin_baixar_backup' %}" class="inline" onsubmit="let pw = prompt('Digite sua senha de administrador para gerar e criptografar este ZIP:'); if(pw){ this.senha_admin.value=pw; return true; } return false;">
                                        {% csrf_token %}
                                        <input type="hidden" name="senha_admin" value="">
                                        <button type="submit" class="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded transition-colors" title="Baixar DB Atual (ZIP)">
                                            <i data-lucide="download" class="w-4 h-4"></i>
                                        </button>
                                    </form>"""

# Patch 2: Baixar Backup Específico
old_link_2 = """                                    <a href="{% url 'sysadmin_baixar_backup_id' b.id %}" class="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors" title="Baixar">
                                        <i data-lucide="download" class="w-4 h-4"></i>
                                    </a>"""

new_form_2 = """                                    <form method="POST" action="{% url 'sysadmin_baixar_backup_id' b.id %}" class="inline" onsubmit="let pw = prompt('Digite sua senha de administrador para gerar e criptografar este ZIP:'); if(pw){ this.senha_admin.value=pw; return true; } return false;">
                                        {% csrf_token %}
                                        <input type="hidden" name="senha_admin" value="">
                                        <button type="submit" class="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors" title="Baixar (ZIP)">
                                            <i data-lucide="download" class="w-4 h-4"></i>
                                        </button>
                                    </form>"""

# Patch 3: Status da Nuvem
old_td_nuvem = """<td class="px-4 py-3 text-gray-400 font-mono text-xs">{{ b.arquivo }}</td>"""
new_td_nuvem = """<td class="px-4 py-3 text-gray-400 font-mono text-xs">
                                    {{ b.arquivo }}
                                    {% if b.enviado_nuvem %}
                                    <span class="ml-2 text-green-400 inline-flex items-center" title="Enviado para Nuvem"><i data-lucide="cloud-check" class="w-4 h-4"></i></span>
                                    {% endif %}
                                </td>"""

if "senha_admin" not in content:
    content = content.replace(old_link_1, new_form_1)
    content = content.replace(old_link_2, new_form_2)
    content = content.replace(old_td_nuvem, new_td_nuvem)
    with open("core/templates/core/pages/sysadmin_dashboard.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Dashboard patcheado com sucesso!")
else:
    print("Já patcheado.")
