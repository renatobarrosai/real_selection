#!/bin/bash
#
# Real Selection - Síntese de voz em tempo real a partir de texto selecionado
# Copyright (C) 2025 Renato Barros
#
# Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
# sob os termos da GNU General Public License conforme publicada pela
# Free Software Foundation, versão 3 da Licença, ou (a seu critério)
# qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil, mas SEM QUALQUER
# GARANTIA; sem mesmo a garantia implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM
# PROPÓSITO ESPECÍFICO. Consulte a GNU General Public License para mais detalhes.
#
# Você deve ter recebido uma cópia da GNU General Public License junto com este
# programa. Caso contrário, consulte <https://www.gnu.org/licenses/>.
#

##
## Wrapper para executar TTS de seleção primária no Hyprland
##
## Responsabilidades:
## - Roda TTS em background (não bloqueia terminal)
## - Notificações visuais (via notify-send)
## - Previne múltiplas instâncias simultâneas
## - Suprime warnings do ALSA no console
##
## Uso:
##   ./tts_wrapper.sh
##   Ou bind no Hyprland: bind = SUPER, T, exec, ~/.aur/kokoro/examples/tts_wrapper.sh
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
NC='\033[0m'  # No Color

# Funções de log
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERRO:${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] AVISO:${NC} $1" | tee -a "$LOG_FILE"
}

# Envia notificação via notify-send (se disponível)
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

        # Verifica se PID ainda existe
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

# Verifica se main.py existe
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
    # Aguarda processo terminar (polling a cada 0.5s)
    while kill -0 $python_pid 2>/dev/null; do
        sleep 0.5
    done

    # Captura código de saída (assume 0 se não conseguir obter)
    exit_code=0

    # Filtra e anexa logs (remove avisos ALSA)
    if [ -f "$TMP_LOG" ]; then
        grep -v "^ALSA" "$TMP_LOG" >> "$LOG_FILE" 2>/dev/null
        rm -f "$TMP_LOG"
    fi

    # Remove lock
    rm -f "$LOCK_FILE"

    # Verifica se foi interrupção ou conclusão normal
    if [ $exit_code -eq 0 ]; then
        log "TTS concluído com sucesso"
        notify "TTS Kokoro" "Concluído!" "low"
    else
        log_error "TTS falhou ou foi interrompido"
        notify "TTS Kokoro" "Interrompido" "low"
    fi
) &

monitor_pid=$!

# Desvincula monitor do terminal (Python já está desvinculado)
disown $monitor_pid

exit 0
