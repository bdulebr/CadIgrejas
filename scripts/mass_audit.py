import os
import datetime

PROJECT_ROOT = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto"
IGNORE_DIRS = {'.git', 'venv', '__pycache__', 'migrations', 'media', 'staticfiles', 'docs', 'node_modules', 'scratch'}
TARGET_EXTS = {'.py', '.html', '.js', '.json', '.css'}

HEADER_TEMPLATE = """{start_comment}
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: {filename}
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: {date_str}
* LOG DE ALTERAÇÕES:
* - {date_str}: Auditoria e padronização global (Goal)
{end_comment}
"""

def get_comment_syntax(ext):
    if ext == '.py':
        return '"""', '"""'
    elif ext == '.html':
        return '<!--', '-->'
    else:
        return '/*', '*/'

def process_file(filepath):
    ext = os.path.splitext(filepath)[1]
    filename = os.path.relpath(filepath, PROJECT_ROOT).replace('\\', '/')

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove trailing whitespace
    stripped_lines = [line.rstrip() + '\n' for line in lines]

    content = "".join(stripped_lines)

    modified = False

    # Check if header exists
    if "PROJETO: Palavra de Vida Enseada - Intranet" not in content:
        start_c, end_c = get_comment_syntax(ext)
        date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        header = HEADER_TEMPLATE.format(
            start_comment=start_c,
            filename=filename,
            date_str=date_str,
            end_comment=end_c
        )

        # Insert header at top, handling python coding/shebang lines if any
        if ext == '.py' and content.startswith('#!'):
            first_newline = content.find('\n')
            content = content[:first_newline+1] + header + content[first_newline+1:]
        else:
            content = header + content

        modified = True

    # If trailing whitespaces were removed or header added, write back
    if "".join(lines) != content or modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False

def main():
    modified_count = 0
    scanned_count = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Ignore dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTS:
                filepath = os.path.join(root, file)
                scanned_count += 1
                try:
                    if process_file(filepath):
                        print(f"Modificado: {file}")
                        modified_count += 1
                except Exception as e:
                    print(f"Erro ao processar {file}: {str(e)}")

    print(f"\\nAuditoria Concluída: {scanned_count} arquivos escaneados, {modified_count} arquivos modificados/corrigidos.")

if __name__ == "__main__":
    main()
