#!/bin/bash
##
## Script para matar processo TTS em execução
##
## Uso: ./tts_kill.sh
## Ou bind no Hyprland: bind = SUPER SHIFT, T, exec, ~/.aur/kokoro/examples/tts_kill.sh
##

LOCK_FILE="/tmp/kokoro_tts.lock"

# Função para enviar notificação
notify() {
    if command -v notify-send &> /dev/null; then
        notify-send -u normal -t 2000 "TTS Kokoro" "$1"
    fi
}

# Função para buscar processo TTS manualmente (fallback)
buscar_processo_tts() {
    # Procura por processo Python rodando ler_selecao_tts.py
    pgrep -f "python.*ler_selecao_tts.py" | head -n 1
}

# Tenta obter PID do lock file
pid=""
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE")

    # Verifica se processo ainda existe
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "Lock file desatualizado (PID: $pid não existe)"
        pid=""  # Limpa para tentar fallback
    fi
fi

# Se não tem PID válido, tenta buscar manualmente
if [ -z "$pid" ]; then
    echo "Buscando processo TTS manualmente..."
    pid=$(buscar_processo_tts)

    if [ -z "$pid" ]; then
        echo "Nenhum processo TTS encontrado"
        rm -f "$LOCK_FILE"
        notify "Nenhum processo TTS rodando"
        exit 0
    fi

    echo "Processo TTS encontrado via busca manual (PID: $pid)"
fi

# Mata processo
echo "Matando processo TTS (PID: $pid)..."
kill "$pid" 2>/dev/null

# Aguarda até 2 segundos para processo terminar
for i in {1..20}; do
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "Processo TTS terminado com sucesso"
        rm -f "$LOCK_FILE"
        notify "TTS interrompido"
        exit 0
    fi
    sleep 0.1
done

# Se ainda estiver rodando, força kill
echo "Forçando término do processo..."
kill -9 "$pid" 2>/dev/null
rm -f "$LOCK_FILE"

notify "TTS forçadamente interrompido"
echo "Processo TTS forçadamente terminado"

exit 0
