import glob

files = [
    "gestao_membros/views.py",
    "midia_lgpd/views.py",
    "ministerio_casais/views.py",
    "visitantes/views.py",
    "ministerio_casais/views_professores.py"
]

target_line = "from intranet.services.whatsapp_service import enviar_whatsapp_template"

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        modified = False
        for i in range(len(lines)):
            if lines[i].startswith(target_line) and lines[i].strip() == target_line:
                if i > 0:
                    prev_line = lines[i-1]
                    spaces = len(prev_line) - len(prev_line.lstrip(' \t'))
                    if spaces == 0 and i > 1:
                        # Try one more above
                        prev_line = lines[i-2]
                        spaces = len(prev_line) - len(prev_line.lstrip(' \t'))
                    lines[i] = prev_line[:spaces] + target_line + "\n"
                    modified = True

        if modified:
            with open(f, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            print(f"Fixed {f}")
    except Exception as e:
        print(f"Error processing {f}: {e}")
