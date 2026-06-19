#!/bin/bash
cd "$(dirname "$0")"

echo "=============================================================="
echo "INICIANDO SERVIDOR DE PRODUCAO LINUX (VPS)"
echo "=============================================================="

# Leitura basica do .env para pegar o modo DEBUG
if grep -q "DEBUG=True" .env; then
    echo "- Debug Mode: [ALERTA] ATIVADO [Vulneravel]"
else
    echo "- Debug Mode: DESATIVADO [Extrema Seguranca]"
fi

echo "- Servidor Web: WAITRESS / HUPPER"
echo "- Arquivos Estaticos: WHITENOISE (Compactados e Cacheados)"
echo "=============================================================="
echo ""

echo "[1/4] Verificando integridade e seguranca de producao..."
source venv/bin/activate
python manage.py check --deploy

echo ""
echo "[2/4] Aplicando atualizacoes no Banco de Dados (Migrate)..."
python manage.py migrate

echo ""
echo "[3/4] Sincronizando Permissoes e Pastas (Bootstrap)..."
python manage.py bootstrap_sistema

echo ""
echo "[4/4] Coletando arquivos estaticos (WhiteNoise)..."
python manage.py collectstatic --noinput

echo ""
echo "Iniciando servicos de producao..."
echo ""

# Exporta variavel para o Django saber (opcional, porem recomendado)
export USE_HTTPS=False

# Inicia o AI Daemon em Background no Linux
echo "[HOT-RELOAD] Iniciando Cão de Guarda (Daemon da IA) em background..."
nohup python manage.py ai_daemon > logs/ai_daemon.log 2>&1 &
DAEMON_PID=$!

echo "[HOT-RELOAD] Iniciando Servidor Web com monitoramento (Hupper)..."
echo "Pressione CTRL+C para derrubar o servidor e o daemon."
echo ""

# Funcao para matar o Daemon quando o servidor parar
cleanup() {
    echo "Parando AI Daemon (PID: $DAEMON_PID)..."
    kill $DAEMON_PID
    exit 0
}
trap cleanup SIGINT SIGTERM

# Inicia Hupper em foreground
hupper -m waitress --port=8005 intranet.wsgi:application
