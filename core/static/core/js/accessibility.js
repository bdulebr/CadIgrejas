document.addEventListener('DOMContentLoaded', () => {
    // === ESTADOS DE ACESSIBILIDADE ===
    let fontSizeLevel = parseInt(localStorage.getItem('access_font_level')) || 0;
    let isHighContrast = localStorage.getItem('access_high_contrast') === 'true';
    let isReading = false;
    let synth = window.speechSynthesis;
    let utterance = null;

    const MIN_FONT_LEVEL = -2;
    const MAX_FONT_LEVEL = 4;

    // Aplica os estados iniciais salvos
    applyFontSize();
    applyHighContrast();

    // === ELEMENTOS DA DOM ===
    const btnIncreaseFont = document.getElementById('btn-access-increase-font');
    const btnDecreaseFont = document.getElementById('btn-access-decrease-font');
    const btnHighContrast = document.getElementById('btn-access-high-contrast');
    const btnReadPage = document.getElementById('btn-access-read-page');
    const accessMenuBtn = document.getElementById('btn-access-menu-toggle');
    const accessMenuPanel = document.getElementById('access-menu-panel');

    // === FUNÇÕES DE FONTE ===
    function applyFontSize() {
        // Multiplicador baseado em um root de 16px (100%). Cada level é +10% ou -10%
        const percentage = 100 + (fontSizeLevel * 10);
        document.documentElement.style.fontSize = `${percentage}%`;
        localStorage.setItem('access_font_level', fontSizeLevel);
    }

    if (btnIncreaseFont) {
        btnIncreaseFont.addEventListener('click', () => {
            if (fontSizeLevel < MAX_FONT_LEVEL) {
                fontSizeLevel++;
                applyFontSize();
            }
        });
    }

    if (btnDecreaseFont) {
        btnDecreaseFont.addEventListener('click', () => {
            if (fontSizeLevel > MIN_FONT_LEVEL) {
                fontSizeLevel--;
                applyFontSize();
            }
        });
    }

    // === FUNÇÕES DE ALTO CONTRASTE ===
    function applyHighContrast() {
        if (isHighContrast) {
            document.documentElement.classList.add('high-contrast-mode');
        } else {
            document.documentElement.classList.remove('high-contrast-mode');
        }
        localStorage.setItem('access_high_contrast', isHighContrast);
    }

    if (btnHighContrast) {
        btnHighContrast.addEventListener('click', () => {
            isHighContrast = !isHighContrast;
            applyHighContrast();
        });
    }

    // === FUNÇÕES DE LEITURA (TEXT-TO-SPEECH) ===
    function readPageContent() {
        if (isReading) {
            synth.cancel(); // Pára de ler
            isReading = false;
            updateReadButtonUI();
            return;
        }

        // Tenta encontrar o texto selecionado primeiro
        let textToRead = window.getSelection().toString().trim();

        // Se nada selecionado, pega o conteúdo principal
        if (!textToRead) {
            const mainContent = document.querySelector('main') || document.querySelector('.main-content') || document.body;
            textToRead = mainContent.innerText || mainContent.textContent;
        }

        // Limpa espaços extras e quebras
        textToRead = textToRead.replace(/\s+/g, ' ').trim();

        if (textToRead && synth) {
            utterance = new SpeechSynthesisUtterance(textToRead);
            utterance.lang = 'pt-BR';
            utterance.rate = 1.1; // Um pouco mais rápido que o padrão

            utterance.onend = () => {
                isReading = false;
                updateReadButtonUI();
            };

            utterance.onerror = () => {
                isReading = false;
                updateReadButtonUI();
            };

            synth.speak(utterance);
            isReading = true;
            updateReadButtonUI();
        }
    }

    function updateReadButtonUI() {
        if (!btnReadPage) return;
        if (isReading) {
            btnReadPage.innerHTML = `<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path></svg> Parar Leitura`;
            btnReadPage.classList.add('bg-red-500', 'text-white', 'hover:bg-red-600');
            btnReadPage.classList.remove('bg-gray-800', 'hover:bg-gray-700');
        } else {
            btnReadPage.innerHTML = `<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg> Ler Texto em Voz Alta`;
            btnReadPage.classList.remove('bg-red-500', 'text-white', 'hover:bg-red-600');
            btnReadPage.classList.add('bg-gray-800', 'hover:bg-gray-700');
        }
    }

    if (btnReadPage) {
        btnReadPage.addEventListener('click', readPageContent);
    }

    // Fecha o synth ao sair da página
    window.addEventListener('beforeunload', () => {
        if (synth && isReading) {
            synth.cancel();
        }
    });

    // === MENU TOGGLE ===
    if (accessMenuBtn && accessMenuPanel) {
        accessMenuBtn.addEventListener('click', () => {
            accessMenuPanel.classList.toggle('hidden');
        });

        // Clica fora para fechar
        document.addEventListener('click', (e) => {
            if (!accessMenuBtn.contains(e.target) && !accessMenuPanel.contains(e.target)) {
                accessMenuPanel.classList.add('hidden');
            }
        });
    }
});
