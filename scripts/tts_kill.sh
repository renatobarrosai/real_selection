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
## Script para interromper processo TTS em execução
##
## Estratégia de busca:
## 1. Tenta obter PID do lock file (/tmp/kokoro_tts.lock)
## 2. Se lock inválido, busca manualmente por "python.*real_selection/main.py"
## 3. Mata processo graciosamente (SIGTERM), força SIGKILL se necessário
##
## Uso:
##   ./tts_kill.sh
##   Ou bind no Hyprland: bind = SUPER SHIFT, T, exec, ~/.aur/kokoro/examples/tts_kill.sh
##

LOCK_FILE="/tmp/kokoro_tts.lock"

# Envia notificação se notify-send disponível
notify() {
    if command -v notify-send &> /dev/null; then
        notify-send -u normal -t 2000 "TTS Kokoro" "$1"
    fi
}

# Busca processo TTS manualmente (fallback caso lock inválido)
buscar_processo_tts() {
    # Procura especificamente por nosso script (real_selection/main.py)
    pgrep -f "python.*real_selection/main.py" | head -n 1
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

# Se não tem PID válido, tenta busca manual
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

# Mata processo (SIGTERM = gracioso)
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

# Se ainda estiver rodando, força kill (SIGKILL)
echo "Forçando término do processo..."
kill -9 "$pid" 2>/dev/null
rm -f "$LOCK_FILE"

notify "TTS forçadamente interrompido"
echo "Processo TTS forçadamente terminado"

exit 0
