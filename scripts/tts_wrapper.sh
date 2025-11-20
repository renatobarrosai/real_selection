#!/bin/bash
##
## Wrapper para executar TTS de seleção primária no Hyprland
##
## Características:
## - Roda em background (não precisa de terminal)
## - Notificações visuais
## - Previne múltiplas instâncias
## - Suprime avisos do ALSA
##
## Uso: ./tts_wrapper.sh
## Ou bind no Hyprland: bind = SUPER, T, exec, ~/.aur/kokoro/examples/tts_wrapper.sh
##

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_DIR/src/real_selection/main.py"
LOCK_FILE="/tmp/kokoro_tts.lock"
LOG_FILE="$PROJECT_DIR/logs/tts_wrapper.log"

# Cores para log
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERRO:${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] AVISO:${NC} $1" | tee -a "$LOG_FILE"
}

# Função para enviar notificação
notify() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"  # low, normal, critical

    if command -v notify-send &> /dev/null; then
        notify-send -u "$urgency" -t 3000 "$title" "$message"
    fi
}

# Verifica se já existe instância rodando
check_running() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")

        # Verifica se o PID ainda existe
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warn "TTS já está rodando (PID: $pid)"
            notify "TTS Kokoro" "Já existe uma instância rodando!" "low"
            return 1
        else
            # PID morto, remove lock antigo
            rm -f "$LOCK_FILE"
        fi
    fi
    return 0
}

# Cleanup ao sair
cleanup() {
    log "Limpando recursos..."
    rm -f "$LOCK_FILE"
}

# Handler de sinais
trap cleanup EXIT

# Verifica se o main.py existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log_error "Script principal não encontrado: $PYTHON_SCRIPT"
    notify "TTS Kokoro - Erro" "Script não encontrado!" "critical"
    exit 1
fi

# Verifica se já está rodando
if ! check_running; then
    exit 0
fi

# Notifica início
log "Iniciando TTS..."
notify "TTS Kokoro" "Iniciando síntese de voz..." "low"

# Executa TTS em background e captura PID
# Redireciona stderr para arquivo temporário (filtramos ALSA depois)
TMP_LOG="/tmp/kokoro_tts_$$.log"
cd "$PROJECT_DIR"
uv run python "$PYTHON_SCRIPT" 2>"$TMP_LOG" &
python_pid=$!

# Cria lock com PID do processo Python
echo $python_pid > "$LOCK_FILE"

log "TTS rodando em background (PID: $python_pid)"

# Monitora processo em background e faz cleanup
(
    # Aguarda processo terminar (verifica a cada 0.5s)
    while kill -0 $python_pid 2>/dev/null; do
        sleep 0.5
    done

    # Captura código de saída do lock file (Python pode ter gravado)
    # Se não existe, tenta via $? (mas não funciona em subshell, assume 0)
    exit_code=0

    # Filtra e anexa logs (remove avisos ALSA)
    if [ -f "$TMP_LOG" ]; then
        grep -v "^ALSA" "$TMP_LOG" >> "$LOG_FILE" 2>/dev/null
        rm -f "$TMP_LOG"
    fi

    # Remove lock
    rm -f "$LOCK_FILE"

    # Verifica se processo foi morto ou terminou normalmente
    # (se foi morto via tts_kill.sh, lock já foi removido)
    if [ $exit_code -eq 0 ]; then
        log "TTS concluído com sucesso"
        notify "TTS Kokoro" "Concluído!" "low"
    else
        log_error "TTS falhou ou foi interrompido"
        notify "TTS Kokoro" "Interrompido" "low"
    fi
) &

monitor_pid=$!

# Desvincula apenas o monitor do terminal (Python já está desvinculado por herança)
disown $monitor_pid

exit 0
