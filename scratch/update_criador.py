import os
import re

file_path = r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\midia_lgpd\templates\midia_lgpd\criador_templates.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Action do form dinâmico
content = content.replace(
    '''<form method="POST" action="{% url 'criar_template_documento' %}" @submit="prepareForm(event)" class="space-y-6">''',
    '''<form method="POST" action="{% if is_edit %}{% url 'editar_template_documento' template.id %}{% else %}{% url 'criar_template_documento' %}{% endif %}" @submit="prepareForm(event)" class="space-y-6">'''
)

# 2. Informações Base e novos campos
info_base = '''                    <div>
                        <label class="block text-sm font-bold text-gray-300 mb-1">Título do Documento</label>
                        <input type="text" name="titulo" required placeholder="Ex: Contrato de Serviço" value="{{ template.titulo|default:'' }}" class="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-brand-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-300 mb-1">Descrição</label>
                        <input type="text" name="descricao" placeholder="Finalidade deste documento" value="{{ template.descricao|default:'' }}" class="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-brand-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-300 mb-1">Tipo de Documento</label>
                        <select name="tipo_documento" required class="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-brand-500 outline-none">
                            <option value="pdf_lgpd" {% if template.tipo_documento == 'pdf_lgpd' %}selected{% endif %}>PDF Assinatura (Contratos)</option>
                            <option value="email" {% if template.tipo_documento == 'email' %}selected{% endif %}>E-mail Automático</option>
                            <option value="pdf_escala" {% if template.tipo_documento == 'pdf_escala' %}selected{% endif %}>PDF de Escala</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-300 mb-1">ID do Sistema <span class="text-xs text-red-400">(Avançado)</span></label>
                        <input type="text" name="identificador_sistema" placeholder="Ex: email_boas_vindas" value="{{ template.identificador_sistema|default:'' }}" class="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-gray-400 focus:ring-2 focus:ring-brand-500 outline-none font-mono text-sm" {% if not request.user.is_superuser %}readonly{% endif %}>
                        <p class="text-[10px] text-gray-500 mt-1">Usado pelo código para encontrar o template exato na hora do disparo.</p>
                    </div>'''

# re.sub the inputs
content = re.sub(
    r'<div>\s*<label class="block text-sm font-bold text-gray-300 mb-1">Título do Documento</label>.*?</div>\s*<div>\s*<label class="block text-sm font-bold text-gray-300 mb-1">Descrição</label>.*?</div>',
    info_base,
    content,
    flags=re.DOTALL
)

# 3. Inject pre-filled campos_json to AlpineJS
alpine_campos = '''            campos: {% if is_edit %}{{ template.campos_json|safe }}{% else %}[
                { nome: 'NOME_PESSOA', label: 'Nome Completo' },
                { nome: 'CPF_PESSOA', label: 'CPF' }
            ]{% endif %},'''

content = re.sub(
    r'campos: \[\s*\{ nome: \'NOME_PESSOA\'.*?\{ nome: \'CPF_PESSOA\'.*?\],',
    alpine_campos,
    content,
    flags=re.DOTALL
)

# 4. Inject initial HTML into GrapesJS canvas
grapes_init = '''                editor = grapesjs.init({
                    container: '#gjs',
                    height: '100%',
                    width: 'auto',
                    fromElement: true,
                    storageManager: false,
                    plugins: ['gjs-blocks-basic'],
                    pluginsOpts: {
                        'gjs-blocks-basic': {
                            blocks: ['text', 'image', 'link', 'column1', 'column2', 'column3']
                        }
                    },
                    canvas: {
                        styles: [
                            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap'
                        ]
                    }
                });
                
                {% if is_edit %}
                editor.setComponents(`{{ template.html_canva|safe }}`);
                editor.setStyle(`{{ template.css_canva|safe }}`);
                {% endif %}'''

content = re.sub(
    r"editor = grapesjs\.init\(\{.*?canvas: \{.*?\}\s*\}\);\s*",
    grapes_init.replace('$', '\\$'),
    content,
    flags=re.DOTALL
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
