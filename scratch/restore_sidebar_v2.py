import os

old_file = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto\scratch\old_dashboard_full.html"
new_file = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html"

with open(old_file, 'r', encoding='utf-8') as f:
    old_lines = f.readlines()

with open(new_file, 'r', encoding='utf-8') as f:
    new_lines = f.readlines()

# Extract top part of old dashboard (lines containing the sidebar and header)
# We want from the beginning until the line `<div class="p-8 space-y-6 flex-grow relative z-0">`
top_lines = []
for line in old_lines:
    if '<div class="p-8 space-y-6 flex-grow relative z-0">' in line:
        top_lines.append(line)
        break
    top_lines.append(line)

# Extract the inner AI content from new dashboard
# We want to drop lines 1 to 7 (which contains `{% extends ...`, `{% block content %}`, `<div class="min-h-screen ...">`)
# And drop the last 2 lines: `</div>` and `{% endblock content %}`
start_idx = 0
for i, line in enumerate(new_lines):
    if '<!-- Header & Saudação -->' in line:
        start_idx = i
        break

end_idx = len(new_lines)
for i in range(len(new_lines)-1, -1, -1):
    if '{% endblock content %}' in new_lines[i]:
        end_idx = i - 1 # exclude the closing div and endblock
        # Wait, there's a `</div>` for min-h-screen that we need to drop.
        break

inner_lines = new_lines[start_idx:end_idx]

# Assemble final lines
final_lines = top_lines + inner_lines + [
    "    </main>\n",
    "</div>\n",
    "{% endblock content %}\n"
]

with open(new_file, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("Dashboard restored successfully via exact line splitting.")
