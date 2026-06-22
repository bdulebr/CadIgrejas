import os

base_path = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\base.html"
dashboard_path = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html"

with open(dashboard_path, 'r', encoding='utf-8') as f:
    dashboard_content = f.read()

# We know the layout starts right after {% block content %}
# and ends right before {% endblock content %} or {% endblock %}

start_marker = '<div class="min-h-screen bg-transparent flex flex-col md:flex-row" x-data="{ sidebarOpen: true }">'
content_marker = '<!-- Área de Cards e Dashboards -->\n        <div class="p-8 space-y-6 flex-grow relative z-0">'
end_marker = '        </div>\n    </main>\n</div>'

if start_marker in dashboard_content and content_marker in dashboard_content:
    top_layout = dashboard_content.split(start_marker)[1].split(content_marker)[0]
    top_layout = start_marker + top_layout + content_marker
    
    # Replace "Painel Geral" with a block
    top_layout = top_layout.replace('<h1 class="text-2xl font-bold text-white">Painel Geral</h1>', '<h1 class="text-2xl font-bold text-white">{% block header_title %}Painel Geral{% endblock %}</h1>')
    
    # Remove it from dashboard
    new_dashboard = dashboard_content.replace(top_layout, '')
    
    # The end marker should be removed from dashboard too
    if end_marker in new_dashboard:
        new_dashboard = new_dashboard.replace(end_marker, '')
    
    # Now let's inject top_layout into base.html
    with open(base_path, 'r', encoding='utf-8') as f:
        base_content = f.read()
        
    main_target = '    <!-- MAIN CONTENT AREA (Alvo do HTMX) -->\n    <main id="main-content" class="flex-grow flex flex-col">\n        {% block content %}\n        {% endblock content %}\n    </main>'
    
    new_main = f"""
    <!-- MAIN CONTENT AREA COM SIDEBAR -->
    {top_layout}
        {{% block content %}}
        {{% endblock content %}}
    {end_marker}
    """
    
    if main_target in base_content:
        new_base = base_content.replace(main_target, new_main)
        
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(new_base)
            
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(new_dashboard)
            
        print("SUCCESS! Layout migrated.")
    else:
        print("FAILED to find main_target in base.html")
else:
    print("FAILED to find markers in dashboard.html")
