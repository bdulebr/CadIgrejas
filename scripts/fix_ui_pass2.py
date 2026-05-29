import os
import glob
import re

def run():
    html_files = glob.glob('**/*.html', recursive=True)
    
    count = 0
    for path in html_files:
        if 'venv' in path or 'base.html' in path or 'login.html' in path or 'painel.html' in path:
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content
        
        # 1. Consertar botões "Voltar" com bg-gray-200 e hover:bg-gray-300
        # Ex: class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-300 rounded-lg font-medium transition-colors"
        # Vamos usar regex para capturar qualquer botão/link de voltar com bg-gray-200
        new_content = re.sub(
            r'class="[^"]*bg-gray-200[^"]*hover:bg-gray-300[^"]*"',
            r'class="px-5 py-2.5 bg-gray-800/80 hover:bg-gray-700 text-white border border-gray-600 rounded-xl font-bold transition-all shadow-lg backdrop-blur-md"',
            new_content
        )

        # Se houver botões "Voltar" que já foram transformados de text-gray-700 para text-gray-300 e usam bg-gray-200
        new_content = re.sub(
            r'class="[^"]*bg-gray-200[^"]*text-gray-300[^"]*"',
            r'class="px-5 py-2.5 bg-gray-800/80 hover:bg-gray-700 text-white border border-gray-600 rounded-xl font-bold transition-all shadow-lg backdrop-blur-md"',
            new_content
        )

        # 2. Consertar hover:bg-gray-50 em tabelas e listas
        new_content = new_content.replace('hover:bg-gray-50', 'hover:bg-gray-800/50')
        new_content = new_content.replace('hover:bg-gray-100', 'hover:bg-gray-700/50')

        # 3. Consertar border-gray-100
        new_content = new_content.replace('border-gray-100', 'border-white/10')
        new_content = new_content.replace('border-gray-200', 'border-white/10')

        # 4. Consertar bg-gray-50 ou bg-gray-100 que sobraram e viraram fundos inteiros brancos
        new_content = new_content.replace('bg-brand-50', 'bg-blue-900/40 backdrop-blur-md border border-blue-500/20 text-white')
        
        # Consertar textos em bubbles bg-brand-100 text-brand-700 -> bg-blue-900 text-blue-300
        new_content = new_content.replace('bg-brand-100', 'bg-blue-900/60 border border-blue-500/30')
        new_content = new_content.replace('text-brand-700', 'text-blue-400')
        new_content = new_content.replace('text-brand-800', 'text-blue-300')
        new_content = new_content.replace('text-brand-900', 'text-white')

        # 5. Consertar inputs e selects brancos (que tem 'border rounded-lg' mas não tem bg-)
        # Para isso vamos usar regex: achar <input ... class="... outline-none">
        # Se não tiver bg-, injetar bg-gray-950/60 border-gray-700/80 text-white
        def fix_inputs(match):
            tag_full = match.group(0)
            if 'bg-' not in tag_full:
                return tag_full.replace('class="', 'class="bg-gray-950/60 border-gray-700/80 text-white ')
            return tag_full

        new_content = re.sub(r'<input[^>]+class="[^"]*"[^>]*>', fix_inputs, new_content)
        new_content = re.sub(r'<select[^>]+class="[^"]*"[^>]*>', fix_inputs, new_content)
        new_content = re.sub(r'<textarea[^>]+class="[^"]*"[^>]*>', fix_inputs, new_content)

        if content != new_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            print(f"Atualizado: {path}")

    print(f"Total de arquivos refinados: {count}")

if __name__ == '__main__':
    run()
