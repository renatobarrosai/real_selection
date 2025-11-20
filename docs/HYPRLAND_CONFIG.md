# Configuração do TTS no Hyprland

Guia completo para configurar atalhos de teclado no Hyprland para o TTS de seleção primária.

## 📋 Arquivos Criados

1. **`tts_wrapper.sh`** - Script principal que roda o TTS
   - Executa em background (não precisa de terminal)
   - Envia notificações visuais
   - Previne múltiplas instâncias simultâneas
   - Suprime avisos do ALSA
   - Log em `logs/tts_wrapper.log`

2. **`tts_kill.sh`** - Script para interromper o TTS
   - Mata processo em execução
   - Envia notificação de confirmação

## 🎯 Configuração Rápida

### 1. Tornar Scripts Executáveis

```bash
chmod +x ~/.aur/kokoro/examples/tts_wrapper.sh
chmod +x ~/.aur/kokoro/examples/tts_kill.sh
```

### 2. Adicionar Atalhos no Hyprland

Edite seu arquivo de configuração do Hyprland (`~/.config/hypr/hyprland.conf`):

```conf
# TTS Kokoro - Ler seleção primária
bind = SUPER, T, exec, ~/.aur/kokoro/examples/tts_wrapper.sh

# TTS Kokoro - Interromper leitura
bind = SUPER SHIFT, T, exec, ~/.aur/kokoro/examples/tts_kill.sh
```

### 3. Recarregar Configuração do Hyprland

```bash
hyprctl reload
# Ou: SUPER + SHIFT + R (se configurado)
```

## 🚀 Uso

### Ler Texto Selecionado

1. **Selecione** um texto em qualquer aplicativo (NÃO use Ctrl+C)
2. Pressione **`SUPER + T`**
3. Aguarde alguns segundos
4. O áudio começará a tocar automaticamente

### Interromper Leitura

- Pressione **`SUPER + SHIFT + T`** a qualquer momento

## 📊 Comportamento

### Primeira Execução
```
[12:34:56] Iniciando TTS...
[Notificação] "TTS Kokoro - Iniciando síntese de voz..."
[Alguns segundos depois: áudio começa a tocar]
[Após terminar]
[12:35:10] TTS concluído com sucesso
[Notificação] "TTS Kokoro - Concluído!"
```

### Tentativa de Executar Durante Leitura
```
[Notificação] "TTS Kokoro - Já existe uma instância rodando!"
```

### Interrupção Manual
```
[Pressionar SUPER + SHIFT + T]
[12:35:05] Matando processo TTS (PID: 12345)...
[12:35:05] Processo TTS terminado com sucesso
[Notificação] "TTS Kokoro - TTS interrompido"
```

## ⚙️ Personalização

### Alterar Atalhos

Edite `~/.config/hypr/hyprland.conf`:

```conf
# Exemplos de atalhos alternativos:

# Usar ALT ao invés de SUPER
bind = ALT, T, exec, ~/.aur/kokoro/examples/tts_wrapper.sh

# Usar outra tecla
bind = SUPER, R, exec, ~/.aur/kokoro/examples/tts_wrapper.sh  # R de "Read"

# Usar F-key
bind = , F9, exec, ~/.aur/kokoro/examples/tts_wrapper.sh
bind = , F10, exec, ~/.aur/kokoro/examples/tts_kill.sh
```

### Desabilitar Notificações

Edite `tts_wrapper.sh` e comente a função `notify`:

```bash
# Comentar esta linha:
# notify "TTS Kokoro" "Iniciando síntese de voz..." "low"
```

Ou desinstale `libnotify`:
```bash
# As notificações serão automaticamente desabilitadas
```

### Alterar Voz ou Velocidade

Edite `examples/ler_selecao_tts.py` (linhas ~362-363):

```python
producer = AudioProducerThread(
    texto=texto,
    audio_queue=audio_queue,
    pipeline=pipeline,
    voz='pf_dora',    # ← Altere aqui
    speed=1.0         # ← Altere aqui (0.8 = lento, 1.2 = rápido)
)
```

## 🐛 Troubleshooting

### Atalho Não Funciona

**Diagnóstico**:
```bash
# Teste o script manualmente
~/.aur/kokoro/examples/tts_wrapper.sh
```

**Verifique**:
1. Scripts são executáveis? (`ls -l examples/*.sh`)
2. Configuração do Hyprland recarregada? (`hyprctl reload`)
3. Caminho correto no bind?

### Notificações Não Aparecem

**Instale libnotify**:
```bash
sudo pacman -S libnotify
```

**Teste**:
```bash
notify-send "Teste" "Mensagem de teste"
```

### Múltiplas Instâncias Rodando

**Mate todos os processos**:
```bash
# Método 1: Usar script kill
~/.aur/kokoro/examples/tts_kill.sh

# Método 2: Manual
pkill -f ler_selecao_tts.py
rm /tmp/kokoro_tts.lock
```

### Script Trava/Não Termina

**Força término**:
```bash
~/.aur/kokoro/examples/tts_kill.sh  # Tenta kill normal
# Se não funcionar:
pkill -9 -f ler_selecao_tts.py
rm /tmp/kokoro_tts.lock
```

### Ver Logs de Execução

```bash
# Log do wrapper
tail -f ~/.aur/kokoro/logs/tts_wrapper.log

# Log do TTS (DEBUG)
tail -f ~/.aur/kokoro/logs/tts_debug.log
```

## 📝 Logs

### Localização
- **Wrapper**: `~/.aur/kokoro/logs/tts_wrapper.log`
- **TTS Debug**: `~/.aur/kokoro/logs/tts_debug.log`
- **Lock file**: `/tmp/kokoro_tts.lock`

### Limpeza de Logs

```bash
# Limpar logs antigos (manter últimos 5 arquivos)
find ~/.aur/kokoro/logs -name "*.log" -mtime +7 -delete
```

## 🔧 Configurações Avançadas

### Executar Sem Notificações (Silencioso)

Crie `tts_wrapper_silent.sh`:
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
"$PROJECT_DIR/.venv/bin/python" "$SCRIPT_DIR/ler_selecao_tts.py" \
    2>&1 | grep -v "^ALSA" > /dev/null &
disown
```

### Auto-start ao Logar

Adicione ao `~/.config/hypr/hyprland.conf`:
```conf
# NÃO recomendado para TTS, mas se quiser pre-carregar:
# exec-once = ~/.aur/kokoro/examples/pre_load_model.sh
```

### Integração com Rofi/Wofi

Crie um menu para escolher voz:
```bash
#!/bin/bash
VOICE=$(echo -e "pf_dora\npm_marcos\naf_bella" | rofi -dmenu -p "Escolha a voz:")
[ -z "$VOICE" ] && exit
# Modifica ler_selecao_tts.py temporariamente com a voz escolhida
# ...
```

## 📋 Checklist de Instalação

- [ ] Scripts executáveis (`chmod +x`)
- [ ] Atalhos adicionados no `hyprland.conf`
- [ ] Hyprland recarregado (`hyprctl reload`)
- [ ] Teste manual funcionando (`./tts_wrapper.sh`)
- [ ] Teste com atalho funcionando
- [ ] Notificações aparecendo
- [ ] Script kill funcionando

## 🎉 Pronto!

Agora você pode:
- **Selecionar** qualquer texto
- **Pressionar SUPER + T**
- **Ouvir** o áudio automaticamente
- **Interromper** com SUPER + SHIFT + T se necessário

**NÃO** precisa:
- ❌ Abrir terminal
- ❌ Copiar texto (Ctrl+C)
- ❌ Executar comandos manualmente

---

**Versão**: 1.0.0
**Data**: 2025-11-20
