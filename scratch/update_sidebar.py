import re

file_path = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the entire <div class="min-h-screen..."> block's starting tag to add x-data for the sidebar
new_content = re.sub(
    r'<div class="min-h-screen bg-transparent flex flex-col md:flex-row">',
    '<div class="min-h-screen bg-transparent flex flex-col md:flex-row" x-data="{ sidebarOpen: true }">',
    content
)

# New sidebar HTML with better UX and collapsible support
new_sidebar = """<!-- BARRA LATERAL (Sidebar Glass) -->
    <aside :class="sidebarOpen ? 'w-full md:w-64' : 'hidden md:flex md:w-20'" class="bg-gray-900/60 backdrop-blur-xl border-r border-white/10 text-white shadow-2xl flex-col relative z-20 transition-all duration-300">
        <div class="p-4 flex items-center justify-between border-b border-white/10">
            <div x-show="sidebarOpen" class="flex-1 text-center">
                {% if sys_config and sys_config.igreja_logo %}
                    <img src="{{ sys_config.igreja_logo.url }}" alt="Logo" class="h-10 mx-auto object-contain">
                {% else %}
                    <h2 class="text-lg font-black tracking-wider text-blue-300">{{ sys_config.igreja_nome|default:"PV ENSEADA"|upper }}</h2>
                {% endif %}
            </div>
            <!-- Botão Recolher/Expandir -->
            <button @click="sidebarOpen = !sidebarOpen" class="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-300 transition-colors mx-auto" title="Recolher/Expandir Menu">
                <i data-lucide="menu" class="w-5 h-5"></i>
            </button>
        </div>
        
        <nav class="flex-grow py-4 overflow-y-auto overflow-x-hidden flex flex-col gap-1 px-3">
            
            <!-- Agrupamento: Pessoal -->
            <div x-show="sidebarOpen" class="text-[10px] uppercase font-bold text-gray-500 tracking-widest pl-3 mt-2 mb-1">Meu Espaço</div>
            
            <a href="{% url 'dashboard' %}" class="flex items-center gap-3 px-3 py-3 bg-blue-600/80 rounded-xl text-white font-bold transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] group" title="Página Inicial">
                <i data-lucide="home" class="w-5 h-5 min-w-[20px]"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Início</span>
            </a>
            
            <a href="{% url 'minhas_escalas' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Minha Agenda de Escalas">
                <i data-lucide="calendar-check" class="w-5 h-5 min-w-[20px] text-blue-400 group-hover:text-blue-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Minhas Escalas</span>
            </a>

            {% if user.nivel_hierarquico != 'membro_voluntario' %}
            <!-- Agrupamento: Liderança -->
            <div x-show="sidebarOpen" class="text-[10px] uppercase font-bold text-gray-500 tracking-widest pl-3 mt-4 mb-1">Liderança</div>
            
            <a href="{% url 'painel_lider' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Gerenciar Minha Equipe">
                <i data-lucide="users" class="w-5 h-5 min-w-[20px] text-yellow-400 group-hover:text-yellow-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Minha Equipe</span>
            </a>

            <a href="{% url 'painel_escalas' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Criar ou Editar Escalas">
                <i data-lucide="calendar-plus" class="w-5 h-5 min-w-[20px] text-yellow-400 group-hover:text-yellow-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Criar Escalas</span>
            </a>
            
            <a href="{% url 'bi_dashboard_geral' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Gráficos e Relatórios">
                <i data-lucide="bar-chart-2" class="w-5 h-5 min-w-[20px] text-yellow-400 group-hover:text-yellow-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Relatórios</span>
            </a>
            {% endif %}
            
            <div x-show="sidebarOpen" class="text-[10px] uppercase font-bold text-gray-500 tracking-widest pl-3 mt-4 mb-1">Recursos</div>
            <a href="{% url 'painel_inventario' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Estoque e Materiais">
                <i data-lucide="box" class="w-5 h-5 min-w-[20px] text-indigo-400 group-hover:text-indigo-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Estoque / Itens</span>
            </a>
            
            {% if user.nivel_hierarquico == 'super_admin' or user.is_superuser %}
            <!-- Agrupamento: Administração -->
            <div x-show="sidebarOpen" class="text-[10px] uppercase font-bold text-red-500 tracking-widest pl-3 mt-4 mb-1">Administração</div>
            
            <a href="{% url 'painel_midia' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Gestão de Arquivos">
                <i data-lucide="folder-open" class="w-5 h-5 min-w-[20px] text-red-400 group-hover:text-red-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Arquivos</span>
            </a>
            <a href="{% url 'departamentos' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Gestão de Departamentos">
                <i data-lucide="layers" class="w-5 h-5 min-w-[20px] text-red-400 group-hover:text-red-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Departamentos</span>
            </a>
            <a href="{% url 'painel_membros' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Todos os Membros">
                <i data-lucide="user-check" class="w-5 h-5 min-w-[20px] text-red-400 group-hover:text-red-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Membros</span>
            </a>
            <a href="{% url 'sysadmin_dashboard' %}" class="flex items-center gap-3 px-3 py-3 text-gray-300 hover:bg-white/10 hover:text-white rounded-xl font-medium transition-colors group" title="Configurações do Sistema">
                <i data-lucide="settings" class="w-5 h-5 min-w-[20px] text-red-400 group-hover:text-red-300"></i>
                <span x-show="sidebarOpen" class="whitespace-nowrap">Configurações</span>
            </a>
            {% endif %}
            
        </nav>
        
        <div class="p-4 border-t border-white/10">
            <form action="{% url 'logout' %}" method="post">
                {% csrf_token %}
                <button type="submit" class="w-full flex items-center justify-center gap-2 p-3 bg-red-600/20 hover:bg-red-600 text-red-300 hover:text-white border border-red-500/30 rounded-xl font-bold transition-colors shadow-sm group" title="Sair do Sistema">
                    <i data-lucide="log-out" class="w-5 h-5 min-w-[20px]"></i>
                    <span x-show="sidebarOpen" class="whitespace-nowrap">Sair</span>
                </button>
            </form>
        </div>
    </aside>"""

# Replace the old sidebar with the new sidebar
new_content = re.sub(
    r'<!-- BARRA LATERAL \(Sidebar Glass\) -->.*?<!-- CONTEÚDO PRINCIPAL -->',
    new_sidebar + '\n\n    <!-- CONTEÚDO PRINCIPAL -->',
    new_content,
    flags=re.DOTALL
)

# Header: Add hamburger button for mobile at the top
new_header = """<!-- Header Topo -->
        <header class="relative z-[9999] bg-gray-900/40 backdrop-blur-md border-b border-white/10 shadow-sm px-4 md:px-8 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-3 w-full md:w-auto">
                <button @click="sidebarOpen = !sidebarOpen" class="md:hidden p-2 bg-gray-800 text-white rounded-lg">
                    <i data-lucide="menu" class="w-6 h-6"></i>
                </button>
                <h1 class="text-2xl font-bold text-white">Painel Geral</h1>
            </div>"""

new_content = re.sub(
    r'<!-- Header Topo -->\s*<header[^>]+>\s*<h1[^>]+>Painel Geral</h1>',
    new_header,
    new_content,
    flags=re.DOTALL
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Dashboard template updated successfully.")
