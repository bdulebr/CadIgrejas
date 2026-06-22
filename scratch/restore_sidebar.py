import re

old_file = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto\scratch\old_dashboard_full.html"
new_file = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html"

with open(old_file, 'r', encoding='utf-8') as f:
    old_content = f.read()

with open(new_file, 'r', encoding='utf-8') as f:
    new_content = f.read()

# Extract the <aside> and <header> from the old content
# It starts at: <div class="min-h-screen bg-transparent flex flex-col md:flex-row" x-data="{ sidebarOpen: true }">
# and ends right after the <header> tag closes.
match_layout = re.search(r'(<div class="min-h-screen bg-transparent flex flex-col md:flex-row".*?</header>)', old_content, re.DOTALL)
if not match_layout:
    print("Could not find the layout wrapper in old dashboard.")
    exit(1)
    
layout_wrapper_top = match_layout.group(1)

# Extract the inner content of the new dashboard (what's inside {% block content %})
match_new_content = re.search(r'{% block content %}\s*(<div class="min-h-screen.*?)(\s*{% if not assinou_lgpd %}.*?)?{% endblock %}', new_content, re.DOTALL)
if not match_new_content:
    print("Could not find the new content block in new dashboard.")
    exit(1)

new_inner_content = match_new_content.group(1)
# Also extract the LGPD modal if it's there
lgpd_modal = match_new_content.group(2) if match_new_content.group(2) else ""

# Wait, the old dashboard also had the LGPD modal just inside the content area.
# Let's extract the LGPD modal from the old dashboard to be safe, or just use the one from new.
match_lgpd_old = re.search(r'({% if not assinou_lgpd %}.*?{% endif %})', old_content, re.DOTALL)
lgpd_old = match_lgpd_old.group(1) if match_lgpd_old else ""

# Construct the final HTML
final_html = """{% extends 'core/base.html' %}
{% load static %}
{% block title %}Intranet PVE - Início{% endblock %}
{% block bg_image %}{% static 'img/bg_home.png' %}{% endblock %}

{% block content %}
""" + layout_wrapper_top + """

        <!-- Área de Cards e Dashboards (NEW AI LAYOUT) -->
        <div class="p-8 space-y-6 flex-grow relative z-0">
            """ + lgpd_old + """
            
            """ + new_inner_content + """
        </div>
    </main>
</div>
{% endblock content %}
"""

with open(new_file, 'w', encoding='utf-8') as f:
    f.write(final_html)
    
print("Dashboard sidebar restored successfully.")
