import os

html_content = """{% load static %}
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Caixa PDV - {{ caixa_atual.operador.username }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        body { background-color: #030712; color: #f3f4f6; overflow: hidden; }
        .glass { background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .cart-item-enter { animation: slideIn 0.2s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
    </style>
</head>
<body class="h-screen flex flex-col" x-data="pdvApp()" 
      @keydown.window.f2.prevent="novaVenda()" 
      @keydown.window.f8.prevent="if(carrinho.length > 0 && !modalPagamento) abrirPagamento()"
      @keydown.window.escape.prevent="if(modalPagamento) { modalPagamento = false; $refs.scannerInput.focus(); } else { window.location.href='/pdv/'; }">

    <!-- Top Bar -->
    <header class="glass h-16 flex justify-between items-center px-6 shrink-0 z-10 border-b border-gray-800">
        <div class="flex items-center gap-4">
            <h1 class="text-2xl font-black text-blue-500 tracking-wider">CAIXA RÁPIDO</h1>
            <span class="px-2 py-1 bg-green-500/20 text-green-400 border border-green-500/30 rounded text-xs font-bold uppercase">PDV 01</span>
            <span class="text-sm text-gray-400 ml-4 border-l border-gray-700 pl-4">Operador: <strong class="text-white">{{ caixa_atual.operador.first_name|default:caixa_atual.operador.username }}</strong></span>
        </div>
        <div class="flex items-center gap-6 text-sm font-bold text-gray-400">
            <div class="flex items-center gap-2"><kbd class="bg-gray-800 px-2 py-1 rounded text-white border border-gray-600">F2</kbd> Nova Venda</div>
            <div class="flex items-center gap-2"><kbd class="bg-blue-600 px-2 py-1 rounded text-white border border-blue-500">F8</kbd> Finalizar</div>
            <a href="{% url 'pdv_dashboard' %}" class="ml-4 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded transition border border-gray-600 flex items-center gap-2"><kbd class="bg-gray-900 px-1 py-0.5 rounded text-[10px]">ESC</kbd> Voltar à Gestão</a>
        </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
        
        <!-- Left Column: Products Grid & Scanner -->
        <div class="w-1/2 p-6 flex flex-col justify-between border-r border-gray-800 relative bg-gray-950/50">
            
            <!-- Hidden global scanner input -->
            <input type="text" x-ref="scannerInput" x-model="codigoScan" @keydown.enter="processarScan()" class="absolute opacity-0 w-0 h-0" autofocus>
            
            <div class="flex justify-between items-end mb-4 shrink-0">
                <h2 class="text-lg font-bold text-white flex items-center gap-2">
                    <i data-lucide="layout-grid" class="w-5 h-5 text-blue-500"></i> Atalhos de Produtos
                </h2>
                <div class="text-xs text-gray-500">Clique para adicionar</div>
            </div>

            <!-- Product Grid -->
            <div class="grid grid-cols-3 lg:grid-cols-4 gap-3 flex-1 overflow-y-auto mb-6 pr-2 custom-scrollbar">
                {% for prod in produtos_rapidos %}
                <button @click="addProdutoGrid({{ prod.id }}, '{{ prod.nome|escapejs }}', {{ prod.preco_venda|stringformat:"f" }})" class="bg-gray-900 hover:bg-blue-600/20 border border-gray-800 hover:border-blue-500 p-3 rounded-2xl flex flex-col items-center justify-center transition-all aspect-square group shadow-sm">
                    <div class="w-10 h-10 rounded-full bg-gray-800 group-hover:bg-blue-500/20 flex items-center justify-center mb-2 transition-colors">
                        <i data-lucide="package" class="w-5 h-5 text-gray-400 group-hover:text-blue-400 transition-colors"></i>
                    </div>
                    <span class="text-xs font-bold text-center text-gray-300 group-hover:text-white line-clamp-2 leading-tight">{{ prod.nome }}</span>
                    <span class="text-sm text-green-400 mt-auto font-black">R$ {{ prod.preco_venda }}</span>
                </button>
                {% empty %}
                <div class="col-span-4 text-center flex flex-col items-center justify-center h-full text-gray-500 py-12">
                    <i data-lucide="inbox" class="w-12 h-12 mb-3 text-gray-700"></i>
                    <p>Nenhum produto cadastrado com estoque no sistema.</p>
                </div>
                {% endfor %}
            </div>

            <!-- Manual Barcode Input Helper -->
            <div class="bg-gray-900 p-4 rounded-xl border border-gray-800 shadow-inner flex items-center shrink-0">
                <i data-lucide="keyboard" class="w-6 h-6 text-gray-500 mr-3"></i>
                <input type="text" placeholder="Digitar código EAN manual e apertar ENTER..." class="bg-transparent border-none outline-none text-lg w-full font-mono text-blue-300 placeholder-gray-600" 
                       x-model="manualCodigo" @keydown.enter="processarScanManual()">
            </div>
        </div>

        <!-- Right Column: Cart and Totals -->
        <div class="w-1/2 flex flex-col bg-gray-900">
            
            <!-- Cart List -->
            <div class="flex-1 overflow-y-auto p-6" id="cartContainer">
                <table class="w-full text-left">
                    <thead>
                        <tr class="text-gray-500 text-sm border-b border-gray-800">
                            <th class="pb-3 font-medium">ITEM</th>
                            <th class="pb-3 font-medium text-center">QTD</th>
                            <th class="pb-3 font-medium text-right">UNITÁRIO</th>
                            <th class="pb-3 font-medium text-right">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template x-for="(item, index) in carrinho" :key="index">
                            <tr class="border-b border-gray-800/50 cart-item-enter" :class="{'bg-red-900/20 opacity-50': item.cancelado}">
                                <td class="py-4">
                                    <span class="text-xs bg-gray-800 px-2 py-0.5 rounded text-gray-400 mr-2" x-text="String(index+1).padStart(3, '0')"></span>
                                    <span class="font-bold text-lg" :class="item.cancelado ? 'line-through text-gray-500' : 'text-white'" x-text="item.nome"></span>
                                </td>
                                <td class="py-4 text-center font-bold text-blue-400" x-text="item.qtd"></td>
                                <td class="py-4 text-right text-gray-400" x-text="'R$ ' + parseFloat(item.preco).toFixed(2)"></td>
                                <td class="py-4 text-right font-bold text-white text-lg" x-text="'R$ ' + (item.preco * item.qtd).toFixed(2)"></td>
                            </tr>
                        </template>
                        <tr x-show="carrinho.length === 0">
                            <td colspan="4" class="text-center py-20">
                                <i data-lucide="shopping-cart" class="w-16 h-16 mx-auto text-gray-800 mb-4"></i>
                                <p class="text-gray-600 font-medium">O carrinho está vazio.</p>
                                <p class="text-gray-700 text-sm mt-1">Clique nos botões ao lado ou use o leitor de barras.</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Totals Box -->
            <div class="glass p-6 border-t border-gray-800 shrink-0">
                <div class="flex justify-between items-end mb-4">
                    <div class="text-gray-400 uppercase tracking-widest font-bold text-sm">Total da Venda</div>
                    <div class="text-gray-500 font-bold" x-show="desconto > 0">Desc: R$ <span x-text="desconto.toFixed(2)"></span></div>
                </div>
                <div class="text-right text-6xl font-black text-green-400 drop-shadow-[0_0_15px_rgba(74,222,128,0.3)]">
                    R$ <span x-text="totalVenda.toFixed(2)">0.00</span>
                </div>
            </div>
            
        </div>
    </div>

    <!-- Modal Pagamento (F8) -->
    <div x-show="modalPagamento" style="display: none;" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
        <div class="bg-gray-900 border border-gray-700 rounded-3xl p-8 max-w-lg w-full shadow-2xl">
            <h2 class="text-3xl font-black text-white mb-6 flex items-center gap-3"><i data-lucide="wallet" class="w-8 h-8 text-green-400"></i> Pagamento</h2>
            
            <div class="bg-gray-950 rounded-xl p-6 mb-6 text-center border border-gray-800">
                <p class="text-gray-400 uppercase text-xs font-bold mb-1">Total a Pagar</p>
                <p class="text-5xl font-black text-green-400">R$ <span x-text="totalVenda.toFixed(2)"></span></p>
            </div>
            
            <div class="space-y-4 mb-6">
                <div>
                    <label class="block text-gray-400 text-sm font-bold mb-2">Forma de Pagamento</label>
                    <select x-model="formaPagamento" class="w-full bg-gray-800 border border-gray-700 rounded-lg p-4 text-white font-bold outline-none focus:border-blue-500">
                        <option value="Dinheiro">Dinheiro</option>
                        <option value="Cartao Credito">Cartão de Crédito</option>
                        <option value="Cartao Debito">Cartão de Débito</option>
                        <option value="PIX">PIX</option>
                    </select>
                </div>
                <div x-show="formaPagamento === 'Dinheiro'">
                    <label class="block text-gray-400 text-sm font-bold mb-2">Valor Recebido (Para Troco)</label>
                    <input type="number" x-model.number="valorRecebido" class="w-full bg-gray-800 border border-gray-700 rounded-lg p-4 text-2xl text-white font-bold outline-none focus:border-blue-500">
                </div>
            </div>
            
            <div x-show="formaPagamento === 'Dinheiro' && valorRecebido > totalVenda" class="bg-blue-900/30 border border-blue-500/30 rounded-xl p-4 mb-6 flex justify-between items-center">
                <span class="text-blue-300 font-bold">TROCO:</span>
                <span class="text-3xl font-black text-blue-400">R$ <span x-text="(valorRecebido - totalVenda).toFixed(2)"></span></span>
            </div>
            
            <button @click="finalizarVendaReal()" class="w-full bg-green-600 hover:bg-green-500 text-white font-black py-4 rounded-xl shadow-[0_0_20px_rgba(34,197,94,0.4)] text-lg flex items-center justify-center gap-2">
                <i data-lucide="check-circle" class="w-6 h-6"></i> CONFIRMAR E FINALIZAR (ENTER)
            </button>
        </div>
    </div>

    <!-- Audio Beeps -->
    <script>
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        function playBeep(type) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            if (type === 'scan') {
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                oscillator.start();
                gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.1);
                oscillator.stop(audioContext.currentTime + 0.1);
            } else if (type === 'error') {
                oscillator.type = 'sawtooth';
                oscillator.frequency.setValueAtTime(150, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                oscillator.start();
                gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.3);
                oscillator.stop(audioContext.currentTime + 0.3);
            } else if (type === 'success') {
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(1046.50, audioContext.currentTime); // C6
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                oscillator.start();
                oscillator.frequency.setValueAtTime(1318.51, audioContext.currentTime + 0.1); // E6
                gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.3);
                oscillator.stop(audioContext.currentTime + 0.3);
            }
        }

        document.addEventListener('alpine:init', () => {
            Alpine.data('pdvApp', () => ({
                carrinho: [],
                codigoScan: '',
                manualCodigo: '',
                desconto: 0,
                
                // Modal
                modalPagamento: false,
                formaPagamento: 'Dinheiro',
                valorRecebido: 0,

                get totalVenda() {
                    const sub = this.carrinho.filter(i => !i.cancelado).reduce((acc, item) => acc + (parseFloat(item.preco) * parseInt(item.qtd)), 0);
                    return Math.max(0, sub - parseFloat(this.desconto));
                },

                init() {
                    // Refocus scanner constantly unless modal is open
                    setInterval(() => {
                        if(!this.modalPagamento && document.activeElement !== this.$refs.scannerInput && document.activeElement.tagName !== 'INPUT') {
                            this.$refs.scannerInput.focus();
                        }
                    }, 500);

                    // We now use @keydown.window.f2 etc. for global shortcuts, 
                    // but we need a listener specifically for Enter when modal is open to finalize
                    window.addEventListener('keydown', (e) => {
                        if(e.key === 'Enter' && this.modalPagamento) {
                            e.preventDefault();
                            this.finalizarVendaReal();
                        }
                    });
                },

                addProdutoGrid(id, nome, preco) {
                    playBeep('scan');
                    // Check if already in cart to increment qty
                    const idx = this.carrinho.findIndex(i => i.id === id && !i.cancelado);
                    if(idx !== -1) {
                        this.carrinho[idx].qtd++;
                    } else {
                        this.carrinho.push({
                            id: id,
                            nome: nome,
                            codigo: 'AVULSO',
                            preco: parseFloat(preco),
                            qtd: 1,
                            cancelado: false
                        });
                    }
                    this.scrollToBottom();
                },

                async processarScan() {
                    if(!this.codigoScan) return;
                    await this.adicionarProdutoByCodigo(this.codigoScan);
                    this.codigoScan = '';
                },

                async processarScanManual() {
                    if(!this.manualCodigo) return;
                    await this.adicionarProdutoByCodigo(this.manualCodigo);
                    this.manualCodigo = '';
                    this.$refs.scannerInput.focus();
                },

                async adicionarProdutoByCodigo(codigo) {
                    try {
                        const res = await fetch(`/pdv/api/produto/${codigo}/`);
                        const data = await res.json();
                        
                        if(data.success) {
                            playBeep('scan');
                            this.carrinho.push({
                                id: data.id,
                                nome: data.nome,
                                codigo: codigo,
                                preco: parseFloat(data.preco_venda),
                                qtd: 1,
                                cancelado: false
                            });
                            this.scrollToBottom();
                        } else {
                            playBeep('error');
                            alert('Produto não encontrado!');
                        }
                    } catch (e) {
                        playBeep('error');
                    }
                },
                
                scrollToBottom() {
                    setTimeout(() => {
                        const el = document.getElementById('cartContainer');
                        if(el) el.scrollTop = el.scrollHeight;
                    }, 50);
                },
                
                abrirPagamento() {
                    this.modalPagamento = true;
                    this.valorRecebido = this.totalVenda;
                },

                async finalizarVendaReal() {
                    if(this.carrinho.length === 0) return;
                    
                    const itens = this.carrinho.filter(i => !i.cancelado);
                    
                    try {
                        const res = await fetch('/pdv/api/venda/finalizar/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' },
                            body: JSON.stringify({
                                itens: itens,
                                forma_pagamento: this.formaPagamento,
                                desconto: this.desconto
                            })
                        });
                        
                        const data = await res.json();
                        if(data.success) {
                            playBeep('success');
                            alert("VENDA CONCLUÍDA COM SUCESSO! TROCO: R$ " + (this.valorRecebido - this.totalVenda).toFixed(2));
                            this.novaVenda();
                        } else {
                            playBeep('error');
                            alert("Erro ao finalizar: " + data.message);
                        }
                    } catch(e) {
                        playBeep('error');
                        alert("Falha de rede ao finalizar venda.");
                    }
                },
                
                novaVenda() {
                    this.carrinho = [];
                    this.desconto = 0;
                    this.modalPagamento = false;
                    this.$refs.scannerInput.focus();
                }
            }));
        });
        lucide.createIcons();
    </script>
</body>
</html>"""

with open(r'c:\Users\MarcosLira\Desktop\Marcos\Projeto\pdv\templates\pdv\frente_caixa.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
