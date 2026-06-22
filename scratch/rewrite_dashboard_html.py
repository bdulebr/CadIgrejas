import os

dashboard_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Intranet PVE - Início{% endblock %}
{% block bg_image %}{% static 'img/bg_home.png' %}{% endblock %}

{% block content %}
<div class="min-h-screen p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-8">
        
        <!-- Header & Saudação -->
        <div class="flex flex-col md:flex-row justify-between items-center bg-gray-900/60 backdrop-blur-xl rounded-2xl p-6 border border-white/5 shadow-2xl">
            <div class="flex items-center gap-4 mb-4 md:mb-0">
                {% if user.foto_perfil %}
                    <img src="{{ user.foto_perfil.url }}" alt="Perfil" class="w-16 h-16 rounded-full border-2 border-blue-500 object-cover shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                {% else %}
                    <div class="w-16 h-16 rounded-full bg-blue-900/50 border-2 border-blue-500 flex items-center justify-center text-blue-400">
                        <i data-lucide="user" class="w-8 h-8"></i>
                    </div>
                {% endif %}
                <div>
                    <h1 class="text-3xl font-black text-white tracking-tight">Olá, {{ user.first_name|default:user.username }}!</h1>
                    <p class="text-blue-400 font-medium">Bom trabalho servindo no Reino.</p>
                </div>
            </div>
            
            <!-- Palavra do Dia (IA) -->
            <div class="bg-black/40 p-4 rounded-xl border border-gray-700/50 max-w-md w-full relative overflow-hidden group">
                <div class="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-400 to-purple-500"></div>
                <div class="flex items-start gap-3 pl-2">
                    <i data-lucide="sparkles" class="w-5 h-5 text-yellow-400 shrink-0 mt-1"></i>
                    <div>
                        <p class="text-white text-sm italic leading-relaxed">"{{ insight_ia.versiculo }}"</p>
                        <p class="text-blue-300 text-xs font-bold mt-2 flex items-center gap-1">
                            <i data-lucide="zap" class="w-3 h-3"></i> Insight: {{ insight_ia.insight }}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- Coluna Esquerda: Escalas e Cultos -->
            <div class="lg:col-span-1 space-y-8">
                
                <!-- Minha Próxima Escala -->
                <div class="bg-gradient-to-br from-blue-900/80 to-gray-900/90 backdrop-blur-md rounded-2xl p-6 border border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.15)]">
                    <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <i data-lucide="calendar-check" class="w-5 h-5 text-blue-400"></i> Minha Próxima Escala
                    </h2>
                    
                    {% if minha_proxima_escala %}
                    <div class="bg-black/30 rounded-xl p-4 border border-white/5">
                        <div class="text-center mb-4">
                            <span class="block text-4xl font-black text-white">{{ minha_proxima_escala.data|date:"d" }}</span>
                            <span class="block text-sm text-blue-300 font-bold uppercase tracking-widest">{{ minha_proxima_escala.data|date:"M Y" }}</span>
                        </div>
                        <div class="space-y-2 text-sm">
                            <div class="flex items-center gap-2 text-gray-300">
                                <i data-lucide="clock" class="w-4 h-4 text-gray-500"></i>
                                <span>{{ minha_proxima_escala.hora_inicio|time:"H:i" }} - {{ minha_proxima_escala.hora_fim|time:"H:i" }}</span>
                            </div>
                            <div class="flex items-center gap-2 text-gray-300">
                                <i data-lucide="users" class="w-4 h-4 text-gray-500"></i>
                                <span>{{ minha_proxima_escala.departamento.nome }}</span>
                            </div>
                            <div class="flex items-center gap-2 text-gray-300">
                                <i data-lucide="briefcase" class="w-4 h-4 text-gray-500"></i>
                                <span class="font-bold text-blue-400">{{ minha_proxima_escala.funcao.nome }}</span>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex flex-col items-center justify-center p-8 text-center text-gray-400 bg-black/20 rounded-xl">
                        <i data-lucide="calendar-x" class="w-10 h-10 mb-2 opacity-50"></i>
                        <p>Nenhuma escala futura encontrada para você.</p>
                    </div>
                    {% endif %}
                </div>

                <!-- Próximos Cultos -->
                <div class="bg-gray-900/60 backdrop-blur-md rounded-2xl p-6 border border-white/5">
                    <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <i data-lucide="church" class="w-5 h-5 text-purple-400"></i> Agenda da Igreja
                    </h2>
                    <div class="space-y-3">
                        {% for culto in proximos_cultos %}
                        <div class="flex items-center gap-4 bg-gray-800/50 hover:bg-gray-800 p-3 rounded-xl transition border border-gray-700/50">
                            <div class="flex flex-col items-center justify-center w-12 h-12 bg-purple-900/30 text-purple-300 rounded-lg shrink-0">
                                <span class="text-lg font-black leading-none">{{ culto.data|date:"d" }}</span>
                                <span class="text-[10px] uppercase font-bold">{{ culto.data|date:"M" }}</span>
                            </div>
                            <div>
                                <h3 class="text-white font-bold text-sm line-clamp-1">{{ culto.titulo }}</h3>
                                <p class="text-gray-400 text-xs">{{ culto.hora_inicio|time:"H:i" }}</p>
                            </div>
                        </div>
                        {% empty %}
                        <p class="text-center text-gray-500 text-sm py-4">Nenhum evento agendado.</p>
                        {% endfor %}
                    </div>
                </div>

            </div>

            <!-- Coluna Central/Direita: Comunicação -->
            <div class="lg:col-span-2 space-y-8">
                
                <!-- Quadro de Notícias -->
                <div class="bg-gray-900/60 backdrop-blur-md rounded-2xl p-6 border border-white/5">
                    <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <i data-lucide="newspaper" class="w-5 h-5 text-green-400"></i> Destaques & Notícias
                    </h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for noticia in noticias_ticker %}
                        <div class="bg-gradient-to-r from-gray-800 to-gray-800/50 p-4 rounded-xl border border-gray-700 hover:border-gray-500 transition group relative overflow-hidden">
                            <div class="absolute right-0 top-0 w-16 h-16 bg-green-500/10 rounded-bl-full group-hover:scale-150 transition-transform duration-500"></div>
                            <h3 class="text-white font-bold mb-2 relative z-10">{{ noticia.titulo }}</h3>
                            <p class="text-gray-400 text-sm relative z-10">{{ noticia.mensagem }}</p>
                        </div>
                        {% empty %}
                        <div class="col-span-full text-center py-8 text-gray-500">Nenhuma notícia no momento.</div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Mural de Recados Internos -->
                <div class="bg-gray-900/60 backdrop-blur-md rounded-2xl p-6 border border-white/5">
                    <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <i data-lucide="message-square" class="w-5 h-5 text-orange-400"></i> Recados dos seus Departamentos
                    </h2>
                    <div class="space-y-4">
                        {% for aviso in avisos %}
                        <div class="flex gap-4 bg-gray-800/50 p-4 rounded-xl border border-gray-700/50 relative overflow-hidden">
                            {% if aviso.fixado %}
                                <div class="absolute top-0 right-0 w-8 h-8 bg-orange-500/20 text-orange-400 flex items-center justify-center rounded-bl-xl"><i data-lucide="pin" class="w-4 h-4"></i></div>
                            {% endif %}
                            <div class="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-white shrink-0">
                                {% if aviso.autor.foto_perfil %}<img src="{{ aviso.autor.foto_perfil.url }}" class="w-full h-full rounded-full object-cover">{% else %}<i data-lucide="user" class="w-5 h-5"></i>{% endif %}
                            </div>
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <h4 class="font-bold text-white">{{ aviso.titulo }}</h4>
                                    <span class="text-xs px-2 py-0.5 bg-gray-700 text-gray-300 rounded">{{ aviso.departamento.nome }}</span>
                                </div>
                                <p class="text-gray-300 text-sm mb-2">{{ aviso.conteudo|truncatechars:150 }}</p>
                                <span class="text-xs text-gray-500">{{ aviso.data_postagem|date:"d M Y - H:i" }} por {{ aviso.autor.first_name }}</span>
                            </div>
                        </div>
                        {% empty %}
                        <div class="text-center py-8 text-gray-500 flex flex-col items-center">
                            <i data-lucide="inbox" class="w-8 h-8 mb-2 opacity-50"></i>
                            <p>O mural está limpo. Nenhum aviso pendente!</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>

{% if not assinou_lgpd %}
<!-- ... Modal LGPD code unchanged ... -->
{% endif %}
{% endblock content %}
"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)
