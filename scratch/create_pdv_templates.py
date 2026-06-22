import os

templates_dir = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto\pdv\templates\pdv"
os.makedirs(templates_dir, exist_ok=True)

html_produtos = """{% extends 'core/base.html' %}
{% block title %}Produtos - Gestão do Caixa{% endblock title %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-black text-white"><i data-lucide="package" class="w-8 h-8 inline text-blue-500"></i> Produtos e Estoque</h1>
            <a href="{% url 'pdv_novo_produto' %}" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg">+ Novo Produto</a>
        </div>
        <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-white/10">
            <table class="w-full text-left text-gray-300">
                <thead>
                    <tr class="border-b border-gray-700 text-gray-400">
                        <th class="py-3 px-4">Nome</th>
                        <th class="py-3 px-4">Código EAN</th>
                        <th class="py-3 px-4">Estoque</th>
                        <th class="py-3 px-4">Preço Venda</th>
                        <th class="py-3 px-4 text-right">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for produto in produtos %}
                    <tr class="border-b border-gray-800 hover:bg-gray-800/50 transition">
                        <td class="py-3 px-4">{{ produto.nome }}</td>
                        <td class="py-3 px-4">{{ produto.codigo_barras|default:"-" }}</td>
                        <td class="py-3 px-4 {% if produto.estoque_atual <= produto.estoque_minimo %}text-red-400 font-bold{% endif %}">{{ produto.estoque_atual }}</td>
                        <td class="py-3 px-4 text-green-400 font-bold">R$ {{ produto.preco_venda }}</td>
                        <td class="py-3 px-4 text-right">
                            <a href="{% url 'pdv_editar_produto' produto.id %}" class="text-blue-400 hover:text-blue-300"><i data-lucide="edit" class="w-5 h-5 inline"></i></a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="5" class="py-6 text-center text-gray-500">Nenhum produto cadastrado.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="mt-4">
            <a href="{% url 'pdv_dashboard' %}" class="text-gray-400 hover:text-white">&larr; Voltar para a Gestão do Caixa</a>
        </div>
    </div>
</div>
{% endblock content %}"""

html_form_produto = """{% extends 'core/base.html' %}
{% block title %}{% if produto %}Editar{% else %}Novo{% endif %} Produto{% endblock title %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-black text-white mb-6">{% if produto %}Editar Produto{% else %}Novo Produto{% endif %}</h1>
        <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-8 border border-white/10">
            <form method="POST" class="space-y-6">
                {% csrf_token %}
                <div class="grid grid-cols-2 gap-6">
                    <div class="col-span-2">
                        <label class="block text-gray-400 text-sm mb-2">Nome do Produto</label>
                        <input type="text" name="nome" value="{{ produto.nome }}" required class="w-full bg-gray-800 text-white rounded p-3 border border-gray-700">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm mb-2">Código de Barras (EAN)</label>
                        <input type="text" name="codigo_barras" value="{{ produto.codigo_barras|default:'' }}" class="w-full bg-gray-800 text-white rounded p-3 border border-gray-700">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm mb-2">Estoque Atual</label>
                        <input type="number" name="estoque_atual" value="{{ produto.estoque_atual|default:0 }}" required class="w-full bg-gray-800 text-white rounded p-3 border border-gray-700">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm mb-2">Preço de Custo (R$)</label>
                        <input type="number" step="0.01" name="preco_custo" value="{{ produto.preco_custo|default:0 }}" class="w-full bg-gray-800 text-white rounded p-3 border border-gray-700">
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm mb-2">Preço de Venda (R$)</label>
                        <input type="number" step="0.01" name="preco_venda" value="{{ produto.preco_venda|default:0 }}" required class="w-full bg-gray-800 text-white rounded p-3 border border-gray-700">
                    </div>
                </div>
                <div class="pt-4 border-t border-gray-700 flex justify-end gap-3">
                    <a href="{% url 'pdv_lista_produtos' %}" class="px-6 py-3 bg-gray-800 text-white rounded-lg font-bold">Cancelar</a>
                    <button type="submit" class="px-6 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg font-bold">Salvar Produto</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock content %}"""

html_livro_caixa = """{% extends 'core/base.html' %}
{% block title %}Livro Caixa - Gestão do Caixa{% endblock title %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-black text-white"><i data-lucide="book-open" class="w-8 h-8 inline text-yellow-500"></i> Livro Caixa</h1>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-white/10">
                <h3 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Últimos Caixas Abertos</h3>
                <ul class="space-y-3 text-sm">
                    {% for cx in caixas|slice:":10" %}
                    <li class="flex justify-between items-center p-3 bg-gray-800/40 rounded">
                        <div>
                            <p class="text-gray-300 font-bold">Caixa {{ cx.id }} - {{ cx.operador.username }}</p>
                            <p class="text-gray-500 text-xs">{{ cx.data_abertura|date:"d/m/Y H:i" }}</p>
                        </div>
                        <span class="px-2 py-1 rounded text-xs font-bold {% if cx.status == 'aberto' %}bg-green-500/20 text-green-400{% else %}bg-gray-600/20 text-gray-400{% endif %}">
                            {{ cx.get_status_display }}
                        </span>
                    </li>
                    {% empty %}
                    <li class="text-gray-500">Nenhum caixa registrado.</li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-6 border border-white/10">
                <h3 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Movimentações Recentes</h3>
                <ul class="space-y-3 text-sm">
                    {% for mov in movimentos %}
                    <li class="flex justify-between items-center p-3 bg-gray-800/40 rounded">
                        <div>
                            <p class="text-gray-300">{{ mov.descricao }}</p>
                            <p class="text-gray-500 text-xs">{{ mov.data_movimento|date:"d/m/Y H:i" }}</p>
                        </div>
                        <span class="font-bold {% if mov.tipo == 'entrada' %}text-green-400{% else %}text-red-400{% endif %}">
                            {% if mov.tipo == 'entrada' %}+{% else %}-{% endif %} R$ {{ mov.valor }}
                        </span>
                    </li>
                    {% empty %}
                    <li class="text-gray-500">Nenhuma movimentação registrada.</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        <div class="mt-6">
            <a href="{% url 'pdv_dashboard' %}" class="text-gray-400 hover:text-white">&larr; Voltar para a Gestão do Caixa</a>
        </div>
    </div>
</div>
{% endblock content %}"""

html_configuracoes = """{% extends 'core/base.html' %}
{% block title %}Configurações PDV{% endblock title %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-black text-white mb-6"><i data-lucide="settings" class="w-8 h-8 inline text-gray-400"></i> Configurações do Caixa</h1>
        <div class="bg-gray-900/50 backdrop-blur-md rounded-xl p-8 border border-white/10">
            <form method="POST" class="space-y-6">
                {% csrf_token %}
                <div class="space-y-4">
                    <label class="flex items-center gap-3 cursor-pointer p-4 bg-gray-800 rounded">
                        <input type="checkbox" name="ativo" {% if config.ativo %}checked{% endif %} class="w-5 h-5 accent-blue-500">
                        <span class="text-gray-300 font-bold">Módulo PDV Ativo Geral</span>
                    </label>
                    <label class="flex items-center gap-3 cursor-pointer p-4 bg-gray-800 rounded">
                        <input type="checkbox" name="imprimir_recibo_automatico" {% if config.imprimir_recibo_automatico %}checked{% endif %} class="w-5 h-5 accent-blue-500">
                        <span class="text-gray-300 font-bold">Imprimir Recibo Automaticamente ao Finalizar Venda</span>
                    </label>
                    <div class="p-4 bg-blue-900/20 border border-blue-500/30 rounded mt-6">
                        <h3 class="text-blue-300 font-bold mb-2">Integração Fiscal (NFC-e)</h3>
                        <label class="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="nfce_ativado" {% if config.nfce_ativado %}checked{% endif %} class="w-5 h-5 accent-blue-500">
                            <span class="text-gray-300 font-bold">Ativar Emissão de NFC-e (Modo Fiscal)</span>
                        </label>
                        <p class="text-xs text-blue-400 mt-2">Para funcionar, os certificados A1 devem estar instalados via SysAdmin.</p>
                    </div>
                </div>
                <div class="pt-6 flex justify-end gap-3">
                    <a href="{% url 'pdv_dashboard' %}" class="px-6 py-3 bg-gray-800 text-white rounded-lg font-bold">Cancelar</a>
                    <button type="submit" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold">Salvar Configurações</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock content %}"""

with open(os.path.join(templates_dir, 'produtos.html'), 'w', encoding='utf-8') as f:
    f.write(html_produtos)
with open(os.path.join(templates_dir, 'form_produto.html'), 'w', encoding='utf-8') as f:
    f.write(html_form_produto)
with open(os.path.join(templates_dir, 'livro_caixa.html'), 'w', encoding='utf-8') as f:
    f.write(html_livro_caixa)
with open(os.path.join(templates_dir, 'configuracoes.html'), 'w', encoding='utf-8') as f:
    f.write(html_configuracoes)
