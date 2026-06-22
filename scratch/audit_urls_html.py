import os
import re
import ast

project_dir = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto"

def get_registered_url_names():
    names = set()
    # Also some hardcoded names that might be generated dynamically or from 3rd party apps
    names.update(['admin:index', 'login', 'logout']) 
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        if 'urls.py' in files:
            filepath = os.path.join(root, 'urls.py')
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'path':
                    for kw in node.keywords:
                        if kw.arg == 'name' and isinstance(kw.value, ast.Constant):
                            names.add(kw.value.value)
    return names

def check_html_urls():
    valid_names = get_registered_url_names()
    # Include admin urls and namespace patterns
    valid_names_prefixes = ['admin:', 'rest_framework:']
    
    missing_urls = []
    
    # regex for {% url 'name' ... %} or {% url "name" ... %}
    pattern = re.compile(r"""\{%\s*url\s+['"]([^'"]+)['"]""")
    
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        if 'templates' in root:
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for url_name in matches:
                            # skip dynamic variables like {% url model.url_name %}
                            if ' ' in url_name or '.' in url_name:
                                continue
                            
                            is_valid = url_name in valid_names
                            if not is_valid:
                                for prefix in valid_names_prefixes:
                                    if url_name.startswith(prefix):
                                        is_valid = True
                                        break
                                        
                            if not is_valid:
                                missing_urls.append((filepath, url_name))
                                
    return missing_urls

missing = check_html_urls()
if missing:
    print("BROKEN LINKS FOUND (NoReverseMatch):")
    for path, name in set(missing):
        print(f"File: {os.path.relpath(path, project_dir)} -> Invalid URL name: '{name}'")
else:
    print("ALL HTML LINKS ARE VALID.")
