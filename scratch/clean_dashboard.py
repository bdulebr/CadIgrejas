import os

dashboard_path = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto\core\templates\core\pages\dashboard.html"

with open(dashboard_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We need to remove from `<div class="min-h-screen...` down to `<div class="p-8 space-y-6 flex-grow relative z-0">`
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '<div class="min-h-screen bg-transparent flex flex-col md:flex-row"' in line:
        start_idx = i
    if '<!-- Área de Cards e Dashboards -->' in line:
        end_idx = i + 1  # includes the div class="p-8..."
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + lines[end_idx+1:]
    
    # Also remove the final </div></main></div> at the end
    # They are the last 3 lines before endblock
    # Let's find endblock
    endblock_idx = -1
    for i, line in enumerate(new_lines):
        if '{% endblock content %}' in line or '{% endblock %}' in line:
            endblock_idx = i
            break
            
    if endblock_idx != -1:
        # Check if the lines before it are </div> \n </main> \n </div>
        # We can just remove the 3 lines before endblock_idx
        # Let's be safer and search backward for </div></main></div>
        pass
        
    # Safer way: just write to string and replace the ending
    content = "".join(new_lines)
    ending_to_remove = "        </div>\n    </main>\n</div>\n{% endblock %}"
    if ending_to_remove in content:
        content = content.replace(ending_to_remove, "{% endblock %}")
    elif "        </div>\n    </main>\n</div>\n{% endblock content %}" in content:
        content = content.replace("        </div>\n    </main>\n</div>\n{% endblock content %}", "{% endblock content %}")
    else:
        # Fallback: remove last 3 divs manually
        content = content.replace("    </main>\n</div>", "")
        
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: dashboard cleaned")
else:
    print(f"FAILED: start={start_idx}, end={end_idx}")
