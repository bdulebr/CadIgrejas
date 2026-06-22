import os
import ast

project_dir = r"c:\Users\MarcosLira\Desktop\Marcos\Projeto"

def get_url_patterns():
    urls = []
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        if 'urls.py' in files:
            filepath = os.path.join(root, 'urls.py')
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'path':
                    if len(node.args) >= 2:
                        view_arg = node.args[1]
                        if isinstance(view_arg, ast.Attribute):
                            # e.g. views.minha_view
                            urls.append(view_arg.attr)
                        elif isinstance(view_arg, ast.Name):
                            # e.g. minha_view
                            urls.append(view_arg.id)
    return set(urls)

def find_dead_views():
    used_views = get_url_patterns()
    dead_views = []
    
    for root, dirs, files in os.walk(project_dir):
        if 'venv' in root or '.git' in root or 'scratch' in root:
            continue
        if 'views.py' in files:
            filepath = os.path.join(root, 'views.py')
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Check if the function takes 'request' as an argument, which usually implies it's a view
                            args = [arg.arg for arg in node.args.args]
                            if 'request' in args and node.name not in used_views:
                                dead_views.append((os.path.relpath(filepath, project_dir), node.name))
                except SyntaxError:
                    pass
    return dead_views

dead = find_dead_views()
for file, func in dead:
    print(f"Dead View Found: {file} -> def {func}(request):")
