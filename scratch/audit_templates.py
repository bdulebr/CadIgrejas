import os
import re

project_dir = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto"

def get_all_templates():
    templates = set()
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        if 'templates' in root:
            for file in files:
                if file.endswith('.html'):
                    # Get the relative path starting from the template dir name
                    # e.g., if path is app/templates/app/page.html -> app/page.html
                    parts = root.split(os.sep)
                    try:
                        idx = parts.index('templates')
                        rel_path = os.path.join(*parts[idx+1:], file) if idx+1 < len(parts) else file
                        # replace windows slashes with forward slashes for matching
                        templates.add(rel_path.replace('\\', '/'))
                    except ValueError:
                        pass
    return templates

def check_views():
    available_templates = get_all_templates()
    missing_templates = []
    
    # regex to find render(..., 'template.html', ...) or TemplateView.as_view(template_name='...')
    pattern = re.compile(r"""render\([^,]+,\s*['"]([^'"]+\.html)['"]""")
    pattern2 = re.compile(r"""template_name\s*=\s*['"]([^'"]+\.html)['"]""")
    
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    matches = pattern.findall(content) + pattern2.findall(content)
                    for t in matches:
                        if t not in available_templates:
                            missing_templates.append((filepath, t))
                            
    return missing_templates

missing = check_views()
if missing:
    print("MISSING TEMPLATES FOUND:")
    for path, t in missing:
        print(f"File: {os.path.relpath(path, project_dir)} -> Missing Template: {t}")
else:
    print("ALL TEMPLATES EXIST.")
