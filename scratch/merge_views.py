import re

# Read the newly generated dashboard view from the backup
with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\scratch\views_current.py', 'r', encoding='utf-8') as f:
    current_content = f.read()

# Extract the new dashboard_view block
# It starts with "def dashboard_view(request):" and ends before "def pwa_manifest"
match_new = re.search(r'(def dashboard_view\(request\):.*?)(?=\ndef pwa_manifest)', current_content, re.DOTALL)
if not match_new:
    print("Could not find the new dashboard_view in views_current.py")
    exit(1)
new_dashboard_code = match_new.group(1)

# Read the restored original views.py
with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\views.py', 'r', encoding='utf-8') as f:
    restored_content = f.read()

# Find the old dashboard_view in the restored file and replace it
# It starts with "def dashboard_view(request):" and ends before "def perfil_view(request):" or whatever is next
# Let's find exactly what is after dashboard_view in the original file
match_old = re.search(r'(def dashboard_view\(request\):.*?)(?=\n@login_required|\ndef )', restored_content, re.DOTALL)
if not match_old:
    print("Could not find the old dashboard_view in restored views.py")
    # try another way
    match_old = re.search(r'(def dashboard_view\(request\):.*?\n)(?=\n[a-zA-Z@])', restored_content, re.DOTALL)

if match_old:
    old_dashboard_code = match_old.group(1)
    new_content = restored_content.replace(old_dashboard_code, new_dashboard_code)
    
    with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\core\views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced dashboard_view!")
else:
    print("Regex failed to match old dashboard_view.")
