import os
import glob
import re

def run():
    html_files = glob.glob('**/*.html', recursive=True)
    
    class_map = {
        'bg-white': 'bg-gray-900/40 backdrop-blur-md border border-white/10',
        'bg-gray-50': 'bg-gray-900/40 backdrop-blur-md border border-white/10',
        'bg-gray-100': 'bg-gray-800/60 backdrop-blur-md border border-white/10',
        'text-gray-800': 'text-white',
        'text-gray-900': 'text-white',
        'text-gray-700': 'text-gray-300',
        'text-gray-600': 'text-gray-300',
        'text-gray-500': 'text-gray-400',
        'border-gray-200': 'border-white/10',
        'border-gray-300': 'border-white/10',
    }

    count = 0
    for path in html_files:
        if 'base.html' in path or 'login.html' in path or 'dashboard.html' in path or 'painel.html' in path:
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        def replacer(match):
            classes = match.group(1).split()
            new_classes = []
            for c in classes:
                if c in class_map:
                    new_classes.extend(class_map[c].split())
                else:
                    new_classes.append(c)
            # Remove duplicates while preserving order
            seen = set()
            new_classes_dedup = [x for x in new_classes if not (x in seen or seen.add(x))]
            return 'class="' + ' '.join(new_classes_dedup) + '"'

        new_content = re.sub(r'class="([^"]*)"', replacer, content)
        
        if content != new_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            print(f"Atualizado: {path}")

    print(f"Total de arquivos atualizados: {count}")

if __name__ == '__main__':
    run()
