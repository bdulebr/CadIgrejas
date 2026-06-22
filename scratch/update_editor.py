import re

file_path = r"C:\Users\MarcosLira\Desktop\Marcos\Projeto\escalas\templates\escalas\editor_manual.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update English words and instructions in HTML
content = content.replace("Nenhum slot configurado para os dias deste mês.", "Nenhuma vaga (função) configurada para os dias deste mês.")
content = content.replace("Configure os slots no painel do departamento primeiro.", "Configure as vagas no painel do departamento primeiro.")
content = content.replace('placeholder="Buscar por nome..."', 'placeholder="Buscar por nome..."\n                <p class="text-[10px] text-gray-400 mt-2"><i data-lucide="info" class="w-3 h-3 inline"></i> Para escalar: Arraste o voluntário, ou <b>clique nele</b> e depois clique na vaga.</p>')

# 2. Inject click selection logic into the javascript
# First, add the selectedItem variable
js_start = """    let draggedItem = null;"""
js_start_replacement = """    let draggedItem = null;
    let selectedItem = null;"""
content = content.replace(js_start, js_start_replacement)

# Add click listener to cards
js_cards = """        card.addEventListener('dragend', function() {
            this.classList.remove('is-dragging');
            draggedItem = null;
        });"""
js_cards_replacement = """        card.addEventListener('dragend', function() {
            this.classList.remove('is-dragging');
            draggedItem = null;
        });
        
        // CLICK SELECTION FOR ELDERLY / MOBILE
        card.addEventListener('click', function(e) {
            if(status_comp !== 'rascunho') return;
            cards.forEach(c => c.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-900/40'));
            this.classList.add('ring-2', 'ring-blue-500', 'bg-blue-900/40');
            selectedItem = this;
        });"""
content = content.replace(js_cards, js_cards_replacement)

# Add click listener to dropzones
js_dropzones = """        zone.addEventListener('dragleave', function() {
            this.classList.remove('dropzone-hover');
        });"""
js_dropzones_replacement = """        zone.addEventListener('dragleave', function() {
            this.classList.remove('dropzone-hover');
        });
        
        // CLICK TO ADD FOR ELDERLY / MOBILE
        zone.addEventListener('click', async function(e) {
            if(status_comp !== 'rascunho') return;
            if(e.target.closest('.btn-remover')) return;
            
            if(!selectedItem) {
                // Ignore empty click if no one selected
                return;
            }
            
            const membro_id = selectedItem.getAttribute('data-id');
            const data_escala = this.getAttribute('data-data');
            const tipo_evento = this.getAttribute('data-evento');
            const funcao_id = this.getAttribute('data-funcao');
            
            const zoneEl = this;
            zoneEl.style.opacity = '0.5';
            
            try {
                const response = await fetch("{% url 'alocar_slot_api' %}", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        comp_id: comp_id,
                        membro_id: membro_id,
                        data_escala: data_escala,
                        tipo_evento: tipo_evento,
                        funcao_id: funcao_id
                    })
                });
                
                const result = await response.json();
                if(result.success) {
                    const fotoHtml = result.foto_url 
                        ? `<img src="${result.foto_url}" class="w-6 h-6 rounded-full object-cover">`
                        : `<div class="w-6 h-6 rounded-full bg-blue-800 flex items-center justify-center text-xs font-bold text-white"><i data-lucide="user" class="w-3 h-3"></i></div>`;
                        
                    const alocadoHtml = `
                        <div class="bg-blue-900/30 border border-blue-500/40 p-2 rounded-lg flex justify-between items-center shadow-sm group">
                            <div class="flex items-center gap-2">
                                ${fotoHtml}
                                <span class="text-xs font-bold text-blue-100 truncate w-32">${result.membro_nome}</span>
                            </div>
                            <button type="button" class="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity btn-remover" data-escala-id="${result.escala_id}">
                                <i data-lucide="x" class="w-4 h-4"></i>
                            </button>
                        </div>
                    `;
                    zoneEl.insertAdjacentHTML('beforeend', alocadoHtml);
                    lucide.createIcons();
                    attachRemoverEvents();
                    
                    const badge = zoneEl.previousElementSibling.querySelector('span:last-child');
                    if(badge) {
                        const parts = badge.innerText.split('/');
                        badge.innerText = (parseInt(parts[0]) + 1) + '/' + parts[1];
                    }
                    
                    // CLEAR SELECTION AFTER ADD
                    cards.forEach(c => c.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-900/40'));
                    selectedItem = null;
                    
                } else {
                    alert('Erro: ' + result.error);
                }
            } catch(err) {
                alert('Falha na comunicação com o servidor.');
            } finally {
                zoneEl.style.opacity = '1';
            }
        });"""
content = content.replace(js_dropzones, js_dropzones_replacement)

# Make sure dropzones cursor becomes pointer
content = content.replace('class="p-2 min-h-[60px] dropzone transition-all flex flex-col gap-2"', 'class="p-2 min-h-[60px] dropzone transition-all flex flex-col gap-2 cursor-pointer hover:bg-white/5 rounded-xl"')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Editor Manual updated successfully.")
