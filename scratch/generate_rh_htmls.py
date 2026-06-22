import os

base_dir = r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\gestao_membros\templates\gestao_membros'

# 1. rh_painel.html
rh_painel_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Dossiê RH & Disciplina - PVE{% endblock %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-black text-white flex items-center gap-3">
                <i data-lucide="shield-alert" class="w-8 h-8 text-red-500"></i> RH e Disciplina
            </h1>
            <a href="{% url 'rh_nova_ocorrencia' %}" class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded font-bold flex items-center gap-2">
                <i data-lucide="book-open" class="w-5 h-5"></i> Registrar Ocorrência
            </a>
        </div>
        
        <p class="text-gray-400 mb-6">Selecione um voluntário para ver o histórico completo, realizar avaliações ou aplicar medidas disciplinares.</p>
        
        <div class="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
            <table class="w-full text-left">
                <thead class="bg-gray-950 text-gray-500 text-sm border-b border-gray-800">
                    <tr>
                        <th class="p-4 font-bold uppercase">Membro</th>
                        <th class="p-4 font-bold uppercase">Departamentos</th>
                        <th class="p-4 font-bold uppercase text-right">Ação</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                    {% for m in membros %}
                    <tr class="hover:bg-gray-800/50 transition">
                        <td class="p-4 text-white font-bold">{{ m.get_full_name|default:m.username }}</td>
                        <td class="p-4 text-gray-400 text-sm">
                            {% for dep in m.departamentos_ativos.all %}
                                <span class="bg-gray-800 px-2 py-1 rounded border border-gray-700">{{ dep.nome }}</span>
                            {% endfor %}
                        </td>
                        <td class="p-4 text-right">
                            <a href="{% url 'rh_dossie_membro' m.id %}" class="px-4 py-2 bg-blue-900/50 hover:bg-blue-600 border border-blue-500/30 text-blue-300 hover:text-white rounded font-bold text-sm inline-flex items-center gap-2 transition">
                                <i data-lucide="folder-open" class="w-4 h-4"></i> Abrir Dossiê
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="3" class="p-8 text-center text-gray-500">Nenhum voluntário encontrado na sua liderança.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(base_dir, 'rh_painel.html'), 'w', encoding='utf-8') as f: f.write(rh_painel_html)

# 2. rh_dossie.html
rh_dossie_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Dossiê: {{ membro.first_name }} - PVE{% endblock %}
{% block content %}
<div class="min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        
        <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
                <a href="{% url 'rh_painel' %}" class="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center text-gray-400 hover:text-white"><i data-lucide="arrow-left" class="w-5 h-5"></i></a>
                <div>
                    <h1 class="text-3xl font-black text-white">{{ membro.get_full_name|default:membro.username }}</h1>
                    <p class="text-gray-400 text-sm">Dossiê e Histórico de Voluntariado</p>
                </div>
            </div>
            <a href="{% url 'rh_aplicar_disciplina' membro.id %}" class="px-4 py-2 bg-red-900/50 border border-red-500 hover:bg-red-600 text-white font-bold rounded flex items-center gap-2 transition">
                <i data-lucide="gavel" class="w-5 h-5"></i> Aplicar Disciplina
            </a>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Coluna Esquerda: Avaliar -->
            <div class="lg:col-span-1 space-y-6">
                
                <div class="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 class="text-white font-bold mb-4 flex items-center gap-2"><i data-lucide="star" class="w-5 h-5 text-yellow-500"></i> Registrar Avaliação</h3>
                    <form action="{% url 'rh_avaliar_membro' membro.id %}" method="POST" class="space-y-4">
                        {% csrf_token %}
                        <div>
                            <label class="block text-gray-400 text-xs uppercase mb-1">Nota (1 a 5)</label>
                            <select name="nota" class="w-full bg-gray-800 text-white rounded border border-gray-700 p-2" required>
                                <option value="5">5 - Excelente</option>
                                <option value="4">4 - Muito Bom</option>
                                <option value="3">3 - Regular</option>
                                <option value="2">2 - Ruim</option>
                                <option value="1">1 - Crítico</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-gray-400 text-xs uppercase mb-1">Observações do Líder</label>
                            <textarea name="comentarios" rows="3" class="w-full bg-gray-800 text-white rounded border border-gray-700 p-2 text-sm" placeholder="Escreva o parecer..." required></textarea>
                        </div>
                        <button type="submit" class="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded">Salvar Avaliação</button>
                    </form>
                </div>

                <div class="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 class="text-white font-bold mb-4">Ações Disciplinares</h3>
                    <div class="space-y-3">
                        {% for acao in acoes %}
                        <div class="bg-gray-950 p-3 rounded border border-red-900/50">
                            <div class="flex justify-between items-start">
                                <span class="text-red-400 font-bold text-sm">{{ acao.get_tipo_display }}</span>
                                <span class="text-gray-500 text-xs">{{ acao.data_aplicacao|date:"d/m/Y" }}</span>
                            </div>
                            <p class="text-gray-400 text-xs mt-1 line-clamp-2">"{{ acao.motivo }}"</p>
                            <a href="{% url 'rh_gerar_pdf_disciplina' acao.id %}" target="_blank" class="mt-2 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                                <i data-lucide="file-text" class="w-3 h-3"></i> Imprimir PDF
                            </a>
                        </div>
                        {% empty %}
                        <p class="text-gray-500 text-sm">Nenhuma punição registrada.</p>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Coluna Direita: Timeline -->
            <div class="lg:col-span-2 space-y-6">
                
                <div class="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 class="text-white font-bold mb-4 flex items-center gap-2 border-b border-gray-800 pb-2">
                        <i data-lucide="history" class="w-5 h-5 text-blue-500"></i> Ocorrências no Livro
                    </h3>
                    <div class="space-y-4">
                        {% for o in ocorrencias %}
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex justify-between items-center mb-2">
                                <h4 class="text-white font-bold">{{ o.titulo }}</h4>
                                <span class="bg-gray-900 text-gray-400 text-xs px-2 py-1 rounded">{{ o.data_ocorrencia|date:"d/m/Y" }}</span>
                            </div>
                            <p class="text-gray-300 text-sm mb-3">{{ o.descricao }}</p>
                            <div class="flex justify-between items-center text-xs text-gray-500">
                                <span>Registrado por: {{ o.autor.first_name }}</span>
                                {% if o.anexo %}
                                <a href="{{ o.anexo.url }}" target="_blank" class="text-blue-400 hover:text-blue-300 flex items-center gap-1"><i data-lucide="paperclip" class="w-3 h-3"></i> Anexo</a>
                                {% endif %}
                            </div>
                        </div>
                        {% empty %}
                        <p class="text-gray-500 text-sm">Membro com ficha limpa (sem ocorrências).</p>
                        {% endfor %}
                    </div>
                </div>

                <div class="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 class="text-white font-bold mb-4 flex items-center gap-2 border-b border-gray-800 pb-2">
                        <i data-lucide="bar-chart" class="w-5 h-5 text-green-500"></i> Histórico de Avaliações
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for av in avaliacoes %}
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex items-center gap-1 mb-2">
                                {% for i in "12345"|make_list %}
                                    <i data-lucide="star" class="w-4 h-4 {% if forloop.counter <= av.nota %}text-yellow-500 fill-yellow-500{% else %}text-gray-600{% endif %}"></i>
                                {% endfor %}
                                <span class="ml-2 text-xs text-gray-400">{{ av.data|date:"d/m/y" }} por {{ av.avaliador.first_name }}</span>
                            </div>
                            <p class="text-gray-300 text-sm italic">"{{ av.comentarios }}"</p>
                        </div>
                        {% empty %}
                        <p class="text-gray-500 text-sm">Nenhuma avaliação realizada ainda.</p>
                        {% endfor %}
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(base_dir, 'rh_dossie.html'), 'w', encoding='utf-8') as f: f.write(rh_dossie_html)

# 3. rh_nova_ocorrencia.html
rh_nova_ocorrencia_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Registrar Ocorrência - PVE{% endblock %}
{% block content %}
<div class="min-h-screen p-8 flex items-center justify-center">
    <div class="w-full max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
        <h2 class="text-2xl font-black text-white mb-6 flex items-center gap-3">
            <i data-lucide="book-open" class="text-blue-500 w-6 h-6"></i> Registrar Ocorrência Geral
        </h2>
        
        <form method="POST" enctype="multipart/form-data" class="space-y-5">
            {% csrf_token %}
            <div>
                <label class="block text-gray-400 text-sm font-bold mb-2">Título Breve</label>
                <input type="text" name="titulo" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 outline-none focus:border-blue-500" placeholder="Ex: Atraso coletivo no ensaio" required>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-gray-400 text-sm font-bold mb-2">Data do Fato</label>
                    <input type="date" name="data_ocorrencia" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 outline-none focus:border-blue-500" required>
                </div>
                <div>
                    <label class="block text-gray-400 text-sm font-bold mb-2">Anexo (Foto/Print/PDF)</label>
                    <input type="file" name="anexo" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-2 text-sm">
                </div>
            </div>

            <div>
                <label class="block text-gray-400 text-sm font-bold mb-2">Membros Envolvidos (Segure CTRL para múltiplos)</label>
                <select name="envolvidos" multiple class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 outline-none h-32 focus:border-blue-500" required>
                    {% for m in membros %}
                    <option value="{{ m.id }}">{{ m.first_name|default:m.username }}</option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <label class="block text-gray-400 text-sm font-bold mb-2">Relato / Descrição Completa</label>
                <textarea name="descricao" rows="4" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 outline-none focus:border-blue-500" required></textarea>
            </div>

            <div class="pt-4 flex justify-end gap-3 border-t border-gray-800">
                <a href="{% url 'rh_painel' %}" class="px-6 py-3 bg-gray-800 text-white rounded-lg font-bold hover:bg-gray-700">Cancelar</a>
                <button type="submit" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow-lg">Salvar Ocorrência</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(base_dir, 'rh_nova_ocorrencia.html'), 'w', encoding='utf-8') as f: f.write(rh_nova_ocorrencia_html)

# 4. rh_aplicar_disciplina.html
rh_aplicar_disciplina_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Ação Disciplinar - PVE{% endblock %}
{% block content %}
<div class="min-h-screen p-8 flex items-center justify-center">
    <div class="w-full max-w-xl bg-gray-900 border border-red-900/50 rounded-xl p-8 shadow-[0_0_50px_rgba(220,38,38,0.1)]">
        <h2 class="text-2xl font-black text-white mb-2 flex items-center gap-3">
            <i data-lucide="gavel" class="text-red-500 w-6 h-6"></i> Aplicar Disciplina
        </h2>
        <p class="text-gray-400 text-sm mb-6">Membro alvo: <strong class="text-white">{{ membro.get_full_name }}</strong></p>
        
        <form method="POST" class="space-y-5" x-data="{ tipo: 'advertencia' }">
            {% csrf_token %}
            <div>
                <label class="block text-gray-400 text-sm font-bold mb-2">Tipo de Sanção</label>
                <select name="tipo" x-model="tipo" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 font-bold text-lg outline-none focus:border-red-500">
                    <option value="advertencia">Advertência Formal</option>
                    <option value="suspensao">Suspensão</option>
                    <option value="expulsao">Desligamento / Expulsão</option>
                </select>
            </div>
            
            <div x-show="tipo === 'suspensao'">
                <label class="block text-gray-400 text-sm font-bold mb-2 text-red-400">Data Final da Suspensão</label>
                <input type="date" name="data_fim_suspensao" class="w-full bg-gray-800 border border-red-900 text-white rounded-lg p-3 outline-none focus:border-red-500" :required="tipo === 'suspensao'">
            </div>

            <div>
                <label class="block text-gray-400 text-sm font-bold mb-2">Motivo Detalhado (Irá para a carta de notificação)</label>
                <textarea name="motivo" rows="4" class="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 outline-none focus:border-red-500" required></textarea>
            </div>

            <div class="flex items-center gap-3 bg-gray-800 p-4 rounded-lg">
                <input type="checkbox" name="enviar_email" checked class="w-5 h-5 accent-red-500">
                <span class="text-gray-300 font-bold">Enviar notificação por e-mail automaticamente (com PDF anexo)</span>
            </div>

            <div class="pt-4 flex justify-end gap-3 border-t border-gray-800">
                <a href="{% url 'rh_dossie_membro' membro.id %}" class="px-6 py-3 bg-gray-800 text-white rounded-lg font-bold hover:bg-gray-700">Cancelar</a>
                <button type="submit" class="px-6 py-3 bg-red-600 hover:bg-red-500 text-white font-black rounded-lg shadow-lg flex items-center gap-2">
                    <i data-lucide="alert-triangle" class="w-5 h-5"></i> APLICAR MEDIDA
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(base_dir, 'rh_aplicar_disciplina.html'), 'w', encoding='utf-8') as f: f.write(rh_aplicar_disciplina_html)

print("HTMLs do RH gerados com sucesso!")
