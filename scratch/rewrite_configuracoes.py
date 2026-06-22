import os

html_content = """{% extends 'core/base.html' %}
{% block title %}Configurações PDV{% endblock title %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-black text-white mb-6 flex items-center gap-3">
            <i data-lucide="settings" class="w-8 h-8 text-gray-400"></i> Configurações e Segurança do Caixa
        </h1>
        
        <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-8 border border-white/10 shadow-2xl">
            <form method="POST" class="space-y-8">
                {% csrf_token %}
                
                <!-- Secao Geral -->
                <div>
                    <h2 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Comportamento do Caixa</h2>
                    <div class="space-y-4">
                        <label class="flex items-center gap-3 cursor-pointer p-4 bg-gray-800 hover:bg-gray-750 transition rounded-xl">
                            <input type="checkbox" name="ativo" {% if config.ativo %}checked{% endif %} class="w-5 h-5 accent-blue-500 rounded">
                            <span class="text-gray-300 font-bold">Módulo PDV Ativo Geral</span>
                        </label>
                        <label class="flex items-center gap-3 cursor-pointer p-4 bg-gray-800 hover:bg-gray-750 transition rounded-xl">
                            <input type="checkbox" name="imprimir_recibo_automatico" {% if config.imprimir_recibo_automatico %}checked{% endif %} class="w-5 h-5 accent-blue-500 rounded">
                            <span class="text-gray-300 font-bold">Imprimir Recibo Automaticamente ao Finalizar Venda</span>
                        </label>
                    </div>
                </div>

                <!-- Secao Acesso (NOVA) -->
                <div>
                    <h2 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2 flex items-center gap-2">
                        <i data-lucide="shield" class="w-5 h-5 text-red-500"></i> Controle de Acesso (Zero-Trust)
                    </h2>
                    <p class="text-sm text-gray-400 mb-4">Selecione quem tem permissão para abrir a tela de vendas. Apenas você (SysAdmin) pode alterar essas regras e ver esta página.</p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <!-- Lider -->
                        <div class="bg-gray-800 p-5 rounded-xl border border-gray-700">
                            <label class="block text-gray-300 font-bold mb-2">Líder do Caixa (Gerente)</label>
                            <select name="lider" class="w-full bg-gray-950 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 outline-none">
                                <option value="">--- Nenhum Líder ---</option>
                                {% for m in membros %}
                                <option value="{{ m.id }}" {% if config.lider_id == m.id %}selected{% endif %}>
                                    {{ m.first_name|default:m.username }} (PIN: {% if m.pin_pdv %}{{ m.pin_pdv }}{% else %}Não def.{% endif %})
                                </option>
                                {% endfor %}
                            </select>
                            <p class="text-xs text-gray-500 mt-2">O líder pode realizar sangrias e estornos (futuro).</p>
                        </div>

                        <!-- Operadores -->
                        <div class="bg-gray-800 p-5 rounded-xl border border-gray-700">
                            <label class="block text-gray-300 font-bold mb-2">Operadores Autorizados</label>
                            <div class="max-h-48 overflow-y-auto bg-gray-950 border border-gray-600 rounded-lg p-3 space-y-2 custom-scrollbar">
                                {% for m in membros %}
                                <label class="flex items-center gap-3 cursor-pointer hover:bg-gray-800 p-1 rounded">
                                    <input type="checkbox" name="operadores" value="{{ m.id }}" 
                                           {% if m in config.operadores.all %}checked{% endif %}
                                           class="w-4 h-4 accent-blue-500">
                                    <span class="text-gray-300 text-sm">
                                        {{ m.first_name|default:m.username }} 
                                        <span class="text-gray-500 text-xs ml-1">(PIN: {% if m.pin_pdv %}{{ m.pin_pdv }}{% else %}N/A{% endif %})</span>
                                    </span>
                                </label>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Secao Fiscal -->
                <div>
                    <h2 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Fiscal</h2>
                    <div class="p-5 bg-blue-900/10 border border-blue-500/20 rounded-xl">
                        <label class="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="nfce_ativado" {% if config.nfce_ativado %}checked{% endif %} class="w-5 h-5 accent-blue-500 rounded">
                            <span class="text-gray-300 font-bold">Ativar Emissão de NFC-e (Modo Fiscal)</span>
                        </label>
                        <p class="text-xs text-blue-400 mt-2 ml-8">Para funcionar, os certificados A1 devem estar instalados via painel master SysAdmin.</p>
                    </div>
                </div>

                <!-- Acoes -->
                <div class="pt-6 flex justify-end gap-3 border-t border-gray-700">
                    <a href="{% url 'pdv_dashboard' %}" class="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-bold transition">Cancelar</a>
                    <button type="submit" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-black shadow-[0_0_15px_rgba(37,99,235,0.4)] transition">
                        SALVAR CONFIGURAÇÕES
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock content %}
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\pdv\templates\pdv\configuracoes.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
